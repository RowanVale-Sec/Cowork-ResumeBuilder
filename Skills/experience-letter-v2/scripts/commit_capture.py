#!/usr/bin/env python3
"""
commit_capture.py — atomic commit of a new experience capture.

Writes three artifacts in a near-atomic way:
  1. Experience letter (.docx) to its destination path
  2. Structured experience yaml to its destination path
  3. Updated career_timeline.json containing the new/updated engagement entry

Design:
  Letter and yaml are written via temp-file + atomic rename (POSIX os.replace).
  Timeline is written LAST, also via temp + rename, after backing up the old one.
  Order matters: if anything fails mid-commit, the worst recoverable state is
  "letter+yaml exist on disk but timeline doesn't yet reference them" — which a
  re-run of this script detects (idempotent by engagement match key) and heals.
  We never leave a timeline entry pointing to a file that isn't there.

Inputs:
  Pass a single JSON payload via --payload <file> OR --payload-json <string>.
  Schema:
  {
    "timeline_path":    "<abs path to career_timeline.json>",
    "workspace_root":   "<abs path — destinations are relative to this>",
    "tenure_id":        "ey-engineering-manager",     # which tenure in timeline
    "engagement":       { ... full engagement entry ... },
    "letter_src":       "<abs path to staged .docx>",
    "letter_dest":      "<relative to workspace_root>",
    "yaml_src":         "<abs path to staged .yaml>",
    "yaml_dest":        "<relative to workspace_root>",
    "match_key":        "name_and_start_month"   # or "id"
  }

Exit codes:
  0   success
  2   preflight / input validation failure (nothing touched)
  3   letter or yaml write failed (nothing touched, or only .tmp leftover cleaned up)
  4   timeline write failed AFTER letter/yaml committed — partial state, but
      letter+yaml are valid; re-run with same payload to heal the timeline.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

try:
    import yaml  # PyYAML — used for optional skills auto-extraction
except ImportError:  # pragma: no cover
    yaml = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    print(f"[commit_capture] {msg}", file=sys.stderr)


def _fsync_file(path: Path) -> None:
    """Force a file's bytes to disk so a later rename is durable."""
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_copy(src: Path, dest: Path) -> None:
    """
    Copy src → dest atomically (from the reader's perspective): write to a temp
    file in dest's directory, fsync, then os.replace onto dest.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=str(dest.parent),
        prefix=f".{dest.name}.",
        suffix=".tmp",
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        shutil.copyfile(src, tmp_path)
        _fsync_file(tmp_path)
        os.replace(tmp_path, dest)
    except Exception:
        # Clean up the temp file if it still exists
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def _atomic_write_json(obj, dest: Path) -> None:
    """Write JSON atomically: temp file in same dir, fsync, replace."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        dir=str(dest.parent),
        prefix=f".{dest.name}.",
        suffix=".tmp",
        encoding="utf-8",
    ) as tmp:
        json.dump(obj, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    try:
        os.replace(tmp_path, dest)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


# ---------------------------------------------------------------------------
# Skills extraction — feeds the per-engagement `skills` block into the timeline
# ---------------------------------------------------------------------------

def _flat_strings(v):
    """Normalise a yaml field into a list of non-empty strings.
    Items may be strings, or dicts with name/description/decision."""
    if v is None:
        return []
    if isinstance(v, list):
        out = []
        for item in v:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                for key in ("name", "description", "decision"):
                    val = item.get(key)
                    if isinstance(val, str) and val.strip():
                        out.append(val.strip())
                        break
        return out
    if isinstance(v, str) and v.strip():
        return [v.strip()]
    return []


def _dedup_preserve(seq):
    """Case-insensitive dedup that preserves first-seen casing and order."""
    seen = set()
    out = []
    for s in seq:
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def extract_skills_from_yaml(yaml_path: Path) -> dict:
    """Build the {tools, concepts, categories} block from a yaml experience letter.

    Mapping (kept simple per design decision — duplicates are OK):
      tools      := technologies.direct ∪ ecosystem ∪ evaluated
      concepts   := approach.frameworks_referenced ∪ approach.design_patterns
                   ∪ keywords.methodologies
      categories := technologies.categories
    """
    if yaml is None:
        _log("PyYAML not available — skipping skills extraction")
        return {"tools": [], "concepts": [], "categories": []}
    if not yaml_path.exists():
        return {"tools": [], "concepts": [], "categories": []}
    with open(yaml_path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}

    tech = doc.get("technologies") or {}
    approach = doc.get("approach") or {}
    kw = doc.get("keywords") or {}

    tools = _flat_strings(tech.get("direct")) + \
            _flat_strings(tech.get("ecosystem")) + \
            _flat_strings(tech.get("evaluated"))
    concepts = _flat_strings(approach.get("frameworks_referenced")) + \
               _flat_strings(approach.get("design_patterns")) + \
               _flat_strings(kw.get("methodologies"))
    categories = _flat_strings(tech.get("categories"))

    return {
        "tools": _dedup_preserve(tools),
        "concepts": _dedup_preserve(concepts),
        "categories": _dedup_preserve(categories),
    }


# ---------------------------------------------------------------------------
# Timeline operations
# ---------------------------------------------------------------------------

def _load_timeline(path: Path) -> dict:
    """
    Tolerant JSON load: some editors pad files with null bytes or whitespace
    past the JSON terminator. Strip that junk before parsing so the script
    doesn't reject timelines that are semantically valid.
    """
    if not path.exists():
        raise FileNotFoundError(f"timeline not found: {path}")
    raw = path.read_bytes()
    # Drop nulls and trailing whitespace — common editor artifacts
    text = raw.replace(b"\x00", b"").decode("utf-8").rstrip()
    # Use raw_decode so any leftover non-JSON trailing bytes are ignored
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text)
    return obj


def _find_tenure(timeline: dict, tenure_id: str) -> dict:
    tenures = timeline.get("tenures") or []
    for t in tenures:
        if t.get("id") == tenure_id:
            return t
    known = [t.get("id") for t in tenures]
    raise ValueError(
        f"tenure_id '{tenure_id}' not found in timeline. Known tenures: {known}"
    )


def _match_existing(engagements: list, new_eng: dict, match_key: str) -> int | None:
    """
    Return the index of an existing engagement that matches, or None.

    match_key:
      - "id": match on engagement.id (case-insensitive)
      - "name_and_start_month": match on lowercased name + start YYYY-MM
    """
    if match_key == "id":
        target_id = (new_eng.get("id") or "").lower()
        if not target_id:
            return None
        for i, e in enumerate(engagements):
            if (e.get("id") or "").lower() == target_id:
                return i
        return None

    if match_key == "name_and_start_month":
        target_name = (new_eng.get("name") or "").strip().lower()
        target_start = (new_eng.get("start") or "")[:7]  # YYYY-MM
        if not target_name:
            return None
        for i, e in enumerate(engagements):
            name = (e.get("name") or "").strip().lower()
            start = (e.get("start") or "")[:7] if e.get("start") else ""
            if name == target_name and (
                # stub with no start matches on name alone; otherwise require start month
                start == target_start or not start
            ):
                return i
        return None

    raise ValueError(f"unknown match_key: {match_key}")


def _merge_engagement(existing: dict, new: dict) -> dict:
    """
    Merge new engagement into existing stub.
    New values win, but we keep existing fields the new payload omits,
    and we drop stub-only markers (`_gap`) once a real letter exists.
    """
    merged = dict(existing)
    for k, v in new.items():
        if v is None:
            continue
        merged[k] = v
    # Once we've got a letter, the stub's _gap note is obsolete
    if merged.get("letter_path") and "_gap" in merged:
        merged.pop("_gap", None)
    return merged


def _apply_engagement(timeline: dict, tenure_id: str, new_eng: dict, match_key: str) -> str:
    """
    Mutates timeline in place. Returns 'updated' or 'added' for logging.
    Also bumps _meta.last_updated.

    Note on skills: if new_eng already has a `skills` block from the caller it
    is preserved. If not, the block is populated by extract_skills_from_yaml
    from the yaml staged alongside the capture (see commit()).
    """
    tenure = _find_tenure(timeline, tenure_id)
    engagements = tenure.setdefault("engagements", [])
    idx = _match_existing(engagements, new_eng, match_key)
    if idx is not None:
        engagements[idx] = _merge_engagement(engagements[idx], new_eng)
        action = "updated"
    else:
        engagements.append(new_eng)
        action = "added"
    # Bookkeeping
    meta = timeline.setdefault("_meta", {})
    meta["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    return action


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

REQUIRED_PAYLOAD_KEYS = {
    "timeline_path", "workspace_root", "tenure_id", "engagement",
    "letter_src", "letter_dest", "yaml_src", "yaml_dest",
}

REQUIRED_ENGAGEMENT_KEYS = {"id", "name", "start", "end", "letter_path", "yaml_path"}


def _validate_payload(payload: dict) -> None:
    missing = REQUIRED_PAYLOAD_KEYS - payload.keys()
    if missing:
        raise ValueError(f"payload missing required keys: {sorted(missing)}")

    eng = payload["engagement"]
    eng_missing = REQUIRED_ENGAGEMENT_KEYS - eng.keys()
    if eng_missing:
        raise ValueError(f"engagement missing required keys: {sorted(eng_missing)}")

    # Source files must exist
    for k in ("letter_src", "yaml_src", "timeline_path"):
        p = Path(payload[k])
        if not p.exists():
            raise FileNotFoundError(f"{k} does not exist: {p}")

    ws_root = Path(payload["workspace_root"])
    if not ws_root.exists() or not ws_root.is_dir():
        raise FileNotFoundError(f"workspace_root missing or not a dir: {ws_root}")

    # Destinations must resolve inside workspace_root (no path-escape)
    for k in ("letter_dest", "yaml_dest"):
        rel = Path(payload[k])
        if rel.is_absolute():
            raise ValueError(f"{k} must be relative to workspace_root (got absolute): {rel}")
        abs_path = (ws_root / rel).resolve()
        if not str(abs_path).startswith(str(ws_root.resolve())):
            raise ValueError(f"{k} escapes workspace_root: {abs_path}")


# ---------------------------------------------------------------------------
# Commit orchestration
# ---------------------------------------------------------------------------

def commit(payload: dict, dry_run: bool = False) -> dict:
    """Returns a dict describing what happened."""
    _validate_payload(payload)

    timeline_path = Path(payload["timeline_path"])
    ws_root = Path(payload["workspace_root"]).resolve()
    letter_dest = (ws_root / payload["letter_dest"]).resolve()
    yaml_dest = (ws_root / payload["yaml_dest"]).resolve()
    letter_src = Path(payload["letter_src"])
    yaml_src = Path(payload["yaml_src"])

    # Preflight: parse the timeline NOW so we fail before touching anything
    timeline = _load_timeline(timeline_path)
    match_key = payload.get("match_key", "name_and_start_month")

    # Auto-populate the engagement's `skills` block from the staged yaml if the
    # caller didn't provide one. Keeps the timeline the single source of truth
    # for skills queries without forcing the skill author to duplicate them.
    eng_in = dict(payload["engagement"])
    if "skills" not in eng_in or not eng_in.get("skills"):
        try:
            eng_in["skills"] = extract_skills_from_yaml(yaml_src)
        except Exception as e:
            _log(f"skills auto-extract failed (non-fatal): {e}")
            eng_in["skills"] = {"tools": [], "concepts": [], "categories": []}

    # Apply engagement changes in memory, but do not write yet
    new_timeline = json.loads(json.dumps(timeline))  # deep copy
    action = _apply_engagement(
        new_timeline, payload["tenure_id"], eng_in, match_key
    )

    if dry_run:
        return {
            "status": "dry_run_ok",
            "action": action,
            "letter_dest": str(letter_dest),
            "yaml_dest": str(yaml_dest),
            "timeline_path": str(timeline_path),
        }

    # -------- Stage 1: letter and yaml commits (each atomic) --------
    # If either fails, nothing has touched the timeline yet.
    try:
        _atomic_copy(letter_src, letter_dest)
        _atomic_copy(yaml_src, yaml_dest)
    except Exception as e:
        _log(f"FAILED during letter/yaml commit: {e}")
        return {"status": "error_letter_or_yaml", "detail": str(e), "exit": 3}

    # -------- Stage 2: timeline backup + atomic rewrite --------
    # At this point the letter & yaml are already in place. If the timeline
    # write fails, the user can re-run with the same payload — this script is
    # idempotent on the engagement match key, so the letter/yaml overwrites
    # will be no-ops and the timeline will be healed.
    backup_path = timeline_path.with_suffix(
        timeline_path.suffix + f".bak-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    )
    try:
        shutil.copyfile(timeline_path, backup_path)
        _fsync_file(backup_path)
    except Exception as e:
        _log(f"FAILED to back up timeline before write: {e}")
        return {
            "status": "error_timeline_backup",
            "detail": str(e),
            "note": "Letter & yaml are in place. Re-run to retry the timeline update.",
            "exit": 4,
        }

    try:
        _atomic_write_json(new_timeline, timeline_path)
    except Exception as e:
        _log(f"FAILED writing timeline: {e}")
        return {
            "status": "error_timeline_write",
            "detail": str(e),
            "backup_path": str(backup_path),
            "note": "Letter & yaml are in place. Re-run to retry the timeline update.",
            "exit": 4,
        }

    return {
        "status": "ok",
        "action": action,
        "letter_dest": str(letter_dest),
        "yaml_dest": str(yaml_dest),
        "timeline_path": str(timeline_path),
        "timeline_backup": str(backup_path),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--payload", help="Path to JSON payload file")
    src.add_argument("--payload-json", help="JSON payload as a string")
    ap.add_argument("--dry-run", action="store_true", help="Validate only; touch nothing")
    args = ap.parse_args()

    try:
        if args.payload:
            payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        else:
            payload = json.loads(args.payload_json)
    except Exception as e:
        _log(f"invalid payload: {e}")
        return 2

    try:
        result = commit(payload, dry_run=args.dry_run)
    except (ValueError, FileNotFoundError) as e:
        _log(f"preflight failure: {e}")
        return 2
    except Exception:
        _log("unexpected failure:")
        traceback.print_exc()
        return 2

    print(json.dumps(result, indent=2))
    return int(result.get("exit", 0)) if result.get("status", "").startswith("error") else 0


if __name__ == "__main__":
    sys.exit(main())
