---
name: experience-letter
description: "Capture detailed project experience through a structured interview and produce a formatted Word document (.docx) that serves as a reusable experience letter. Use this skill whenever the user wants to: document their experience on a project, create an experience letter, capture what they did on a project/engagement, build an experience block, or says things like 'document my experience', 'capture my project work', 'create experience letter for Project X', 'I want to record what I did on this project'. Also trigger when the user mentions experience blocks, project retrospective capture, or wants to preserve project knowledge for future resume building. This skill focuses ONLY on capturing and documenting experience — it does NOT tailor content to a job description."
---

# Experience Letter Capture Skill

## Purpose

Capture a user's project experience through a structured, conversational interview and produce a polished Word document (.docx) that:

1. Preserves rich detail about what they did, how they did it, and why it mattered
2. Is structured so that Claude (or any AI) can later parse it to generate tailored resumes for specific job descriptions
3. Serves as a standalone professional experience letter the user can reference or share
4. Is registered in the user's `career_timeline.json` so every future resume build can discover it

## Important Principles

- **You are an interviewer, not a form filler.** Ask follow-up questions. Probe for specifics. Push for the "so what."
- **Capture the user's authentic framing.** Don't rewrite their experience into generic corporate language. Preserve their unique perspective and terminology.
- **Go deep on decisions and innovations.** What did the user decide that someone else might not have? What was novel about their approach?
- **Quantify relentlessly.** Even rough estimates are better than nothing. Ask: "How many? How long? How big? What changed?"
- **Capture keywords naturally.** The document should contain industry terms, framework names, technology names, and methodology names as they naturally appear — these become searchable later.
- **Anchors over prose for any claim a resume might cite.** See Step 10's anchor guidance; this is what makes resumes refactor-safe later.

---

## Workflow

### Step 0 — Read the timeline BEFORE interviewing

Before asking the user anything, load `career_timeline.json` from the workspace root. It lives next to the user's Experience/, Resumes/, and Cover Letters/ folders. Read it in full and answer these questions to yourself:

1. **Has the user already told me the project name?** If yes, scan `tenures[].engagements[]` for an existing entry that matches either the engagement's `id` or its `name` + `start` month. A match with `letter_path: null` or a `_gap` note is a **stub** — the user previously sketched out this engagement and is now filling it in. A match with a populated `letter_path` means a letter already exists for this engagement; confirm with the user whether they want to replace it or make a new one.
2. **If there's a stub, pre-fill the interview.** Use any fields the stub already has — role, dates, engagement type, tenure it belongs under — as starting assumptions. Say something like "Your timeline already has a stub for this — you listed it as Senior Cloud Security Architect, Oct 2021 to Dec 2021. That still right?" Then skip or breeze through those questions in the interview.
3. **If there's no stub, do NOT create one up-front.** It's tempting to write a placeholder before starting the interview, but don't — a stub written on assumptions drifts from what you actually learn. Stubs get created at the END of capture, in the same atomic commit that saves the letter (Step 11). That way the timeline only ever records what was actually captured.
4. **Which tenure does this engagement belong under?** Use the engagement's start/end to pick the right `tenures[].id`. If the dates straddle two tenures or are ambiguous, ask the user explicitly before proceeding — don't guess.

If `career_timeline.json` doesn't exist, note this and proceed anyway; the commit step in Step 11 will create it.

### Step 1: Initial Context

Collect the basics first:

- Project name or codename (this becomes the engagement's `id` as a slug)
- Organization (can be anonymized)
- User's role/title on the project
- User's **formal title at the employer** at the time (may differ from role on the engagement)
- Engagement type (full-time, contract, consulting, advisory)
- Duration (start/end in YYYY-MM)
- Team size and user's position within the team

### Step 2: The Problem & Why It Mattered

Ask the user to describe:

- What business problem or need existed?
- Why did it matter? What was at stake if it wasn't solved?
- Who was the audience / consumer of the work?
- What was the scope? (single team, department, enterprise-wide, multi-org)

**Probe deeper:** "What would have happened if this project didn't exist?" and "Who was most affected by this problem?"

### Step 3: Approach & Methodology

This is where the richness lives. Explore:

- Was this greenfield, a redesign, an assessment, a migration?
- How did you structure the work? What was your methodology?
- What **frameworks, standards, or references** did you use? (capture for yaml — `approach.frameworks_referenced`)
- What design patterns, architectures, or models did you create?
- What were the key decisions you made? Why those decisions?
- What was novel or innovative about your approach?

**Probe deeper:** "What did you do that someone else in this role might NOT have done?" and "What was the hardest technical or strategic decision?"

### Step 4: Deliverables & Outputs

Capture what was actually produced:

- What were the primary deliverables?
- Who consumed each deliverable and how?
- Is it a one-time output or a living document?
- Were there secondary or supporting deliverables?

### Step 5: Technologies, Concepts & Categories (Skills Capture)

This step produces three things that together form the engagement's `skills` block, which the commit script writes into `career_timeline.json`. Resume-enhancer reads the timeline directly — this is where every keyword it matches on comes from — so spend real time here.

Capture three layers. Ask each explicitly; don't assume answers carry between layers.

**5a. Tools (named products, libraries, platforms, services)**

Split into three buckets — the yaml distinguishes them because resume builders treat them differently:

- **Direct** — what you actually worked with hands-on. Names of products, SDKs, CLIs, libraries, cloud services.
- **Ecosystem** — technologies present in the broader project environment you interacted with indirectly (e.g., the CI system, the SIEM, the ticketing platform that fed the work).
- **Evaluated** — vendor tools or platforms you formally assessed but didn't necessarily adopt.

Ask by example: "What tools did you actually touch day-to-day?" then "What was around it in the environment?" then "What did you evaluate but didn't ship?"

**5b. Concepts (frameworks, methodologies, patterns)**

These are the *non-product* things — standards, methodologies, design patterns, threat-modeling approaches. Recruiters grep for these hard.

Prompt with examples across the landscape:

- Standards / frameworks: NIST CSF, NIST SP 800-53, CIS Benchmarks, CIS Controls, ISO 27001, SOX, OWASP Top 10, OWASP LLM Top 10, MITRE ATT&CK, MITRE ATLAS, NIST AI RMF, COBIT, PASTA, STRIDE, CVSS
- Methodologies / patterns: Shift-Left, Zero Trust, Defense in Depth, Least Privilege, Policy-as-Code, Shared-Responsibility, RACI, Orchestrator pattern, Architecture-Aware Threat Modeling, SBOM, Agile Security Assessment, Sprint-Integrated Remediation

Ask: "Which of these (or others) did you actually apply on this engagement — not just read about?"

**5c. Categories (high-level technical domains)**

One-word-ish domain labels. These are the broad buckets the engagement fits into.

Prompt with examples: Cloud Security, CSPM, CNAPP, DevSecOps, IAM, AppSec, Container Security, Kubernetes Security, LLM Security, Agentic AI Security, Threat Modeling, Supply Chain Security, Data Security, TDR, SPM, SDLC Security, Product Security, Security Architecture, Security Operations.

Ask: "How would you categorize the engagement's technical domains — the labels you'd expect to see in a resume Skills section?"

**Notes for the capture author:**

- Duplicates across engagements are fine — they signal stronger experience. Don't de-dup across engagements.
- If the project was research/strategy-focused with no direct coding, capture that explicitly and let **direct** be empty — but still fill concepts and categories.
- These three lists flow through `extract_skills_from_yaml` (in `commit_capture.py`) into `career_timeline.json`'s per-engagement `skills` block. That's the read path for resume-enhancer.

### Step 6: Stakeholders & Influence

Map the human landscape, and for each group capture **seniority level** (this matters a lot for resume framing):

- Who did you **present to**? At what level? (IC / Manager / Director / VP / C-suite / Board)
- Who did you **collaborate with**? (teams, roles)
- Whose work **changed** because of yours?

### Step 7: Leadership Activities

Capture activities beyond individual contribution:

- Executive presentations
- Published documents (whitepapers, RFCs, playbooks)
- Workshops or training sessions delivered
- Vendor evaluations conducted
- Mentoring or knowledge transfer
- Cross-functional coordination
- Strategic influence beyond immediate scope

### Step 8: Impact & Outcomes

Push hard for specifics:

- What **quantitative** outcomes can you cite? For each, also note the confidence level — measured / estimate / self-reported — so resume builders don't overclaim.
- What **qualitative** outcomes matter?
- How widely was your work adopted?
- How long will this work remain relevant?

**Probe deeper:** "If you had to put a number on it, even a rough one..." and "What's different now because of your work?"

### Step 9: Proudest Achievement

Ask: "What's the single thing from this project you'd want front-and-center on any resume? The one accomplishment that best represents your value?"

Capture:

- A one-sentence headline
- A 2-3 sentence story expanding on it
- Why it matters / what it demonstrates about the user

---

### Step 9.5 — Capture Completeness Checklist

Before producing any files, run through this checklist explicitly with the user. Read each item, check if it was captured, and for anything missing, ask the user one more time. If they genuinely can't or won't provide a value, accept "skip" — but record the skip in `_capture.missing` so resume builders know to treat that claim with lower confidence.

Required fields (flag every gap, prompt the user, proceed on user confirmation):

- [ ] **Dates** — both `duration.start` AND `duration.end` (YYYY-MM)
- [ ] **Role title at the time** — the user's formal employer-side title when this ran (not just the engagement role)
- [ ] **Team size** — rough is fine ("4-8 people"); "I don't remember" is not
- [ ] **Technologies: direct** — at least one, unless the engagement was strategy/research-only (note that explicitly)
- [ ] **Technologies: evaluated** — at least one if any vendor assessment happened
- [ ] **Technologies: ecosystem** — at least one
- [ ] **Concepts / frameworks / methodologies** — at least three total across `approach.frameworks_referenced`, `approach.design_patterns`, and `keywords.methodologies` (covers the `concepts` bucket in the timeline skills block)
- [ ] **Technical categories** — at least one entry in `technologies.categories` (feeds the `categories` bucket in the timeline skills block)
- [ ] **Quantitative impact** — at least one metric with value + confidence level
- [ ] **Qualitative impact** — at least one
- [ ] **Stakeholder levels** — at least one `presented_to` entry with a level (IC / Manager / Director / VP / C-suite / Board)

Say something like: "Quick completeness check before I save this — I want to flag a few things we haven't pinned down. [List the gaps.] Can you take one more pass? Totally fine to say 'skip' on any of these if you really don't know — I'll just mark them so future resumes don't overclaim."

Record the user's choice per field. If they skip any, set `_capture.status: incomplete` and list the skipped dotted paths in `_capture.missing`. If all confirmed, set `status: complete`.

### Step 10 — Generate the Word Document AND the YAML (with anchors)

After collecting all information, generate both artifacts. **Stage them in a temp location first** — do not copy to their final destinations directly. Step 11 will commit them atomically.

Temp staging:

- `<tmp>/Experience_Letter_<ProjectName>.docx`
- `<tmp>/<engagement-id>.yaml`

Use any writable temp dir (e.g., `/sessions/<session-id>/stage-<engagement-id>/`). Don't put them in `/mnt/user-data/outputs/` until Step 11 renames them into place.

#### Word document

Use the docx skill to generate the .docx. Read `/mnt/skills/public/docx/SKILL.md` (or the installed docx skill) for instructions.

Document structure:

```
EXPERIENCE LETTER
Project: [Name] | Role: [Title]
Organization: [Org] | Duration: [Period]

CONTEXT
[2-3 paragraphs: the problem, why it mattered, scope and audience]

APPROACH & METHODOLOGY
[2-4 paragraphs: how the work was structured, frameworks used,
design patterns created, key decisions made, innovations introduced.
This is the richest section — preserve all technical detail.]

KEY DELIVERABLES
[Bullet list of primary and secondary deliverables with brief
descriptions and who consumed them]

TECHNOLOGY LANDSCAPE
[Paragraph or grouped list of technologies — direct, ecosystem,
evaluated. Include categories/domains if applicable.]

STAKEHOLDER ENGAGEMENT
[Brief section on who was presented to, collaborated with, influenced]

LEADERSHIP & CROSS-FUNCTIONAL ACTIVITIES
[Bullet list of leadership activities beyond IC contribution]

IMPACT & OUTCOMES
[Quantitative metrics (even estimates) followed by qualitative outcomes.
Include adoption and longevity notes.]

PROUDEST ACHIEVEMENT
[The headline achievement with supporting narrative]

---
KEYWORD INDEX
[A flat comma-separated list of all relevant technical terms,
domain terms, methodology names, and skill keywords that appeared
naturally in this document. This section exists to help future
AI-assisted resume generation identify relevant terms quickly.]
```

Formatting:

- Clean, professional formatting — no flashy colors
- Heading 1: Document title and major sections (dark navy, 14pt bold)
- Heading 2: Sub-sections if needed (medium blue, 12pt bold)
- Body text: 11pt Arial, comfortable line spacing
- Bullets: Use proper docx-js bullet numbering (never unicode bullets)
- Bottom border under title section as visual separator
- Include generation date in subtle footer text
- Page size: US Letter with 1-inch margins

#### YAML (with provenance anchors)

Use `references/experience-block-template.yaml` as the structural guide. The critical addition in v2: **every bullet-worthy claim carries a stable `id:`** (a provenance anchor). Resume bullets later bind to these ids, not to free text.

Anchor naming convention — dotted path, all lowercase, hyphenated:

```
<engagement-id>.<section>.<field-or-slug>
```

Examples:

- `cspm-transformation.impact.quantitative.attack-surface`
- `cspm-transformation.approach.decisions.multi-cloud-normalization`
- `cspm-transformation.leadership.activities.published-rfc`

Rules:

1. The `<engagement-id>` prefix **must match** the `id:` used in `career_timeline.json` for this engagement.
2. Anchors are immutable once saved. If you need to restructure later, deprecate (`deprecated: true`, `superseded_by:`) rather than renaming.
3. Every list item a resume might cite gets its own id. Single-value fields that might be cited standalone (headline stats, proudest_achievement.headline) get an id too.
4. Keep ids short and stable against rewording. Prefer `attack-surface` over `reduced-attack-surface-60pct` — the number may drift; the concept won't.

Fill the `_capture:` block from Step 9.5's checklist results before saving.

### Step 11 — Atomic Commit (letter + yaml + timeline)

**Don't copy files to their final destinations by hand.** Use the bundled commit script — it's the only supported way to finalize a capture:

```
python <skill-dir>/scripts/commit_capture.py --payload <tmp>/payload.json
```

Build the payload JSON from everything you've captured. Schema:

```json
{
  "timeline_path":    "<abs path to career_timeline.json>",
  "workspace_root":   "<abs path, destinations are relative to this>",
  "tenure_id":        "<which tenure this engagement belongs under>",
  "engagement": {
    "id":                 "<slug, e.g. cspm-transformation>",
    "name":               "<human-readable project name>",
    "role_in_engagement": "<role on the engagement>",
    "start":              "YYYY-MM",
    "end":                "YYYY-MM or 'present'",
    "letter_path":        "<relative to workspace_root>",
    "yaml_path":          "<relative to workspace_root>",
    "engagement_type":    "<full-time | consulting | advisory | ...>"
  },
  "letter_src":  "<abs path to the staged .docx from Step 10>",
  "letter_dest": "<relative, e.g. Experience/Security Engineer (...)/Experience_Letter_X.docx>",
  "yaml_src":    "<abs path to the staged yaml>",
  "yaml_dest":   "<relative, e.g. Experience/.../x.yaml>",
  "match_key":   "name_and_start_month"
}
```

What the script does (and why this matters):

1. **Preflight** — parses the timeline, validates the payload, confirms source files exist and destinations don't escape the workspace. If anything fails here, nothing on disk is touched.
2. **Writes the letter** to its destination via temp file + `os.replace` (POSIX atomic rename).
3. **Writes the yaml** the same way.
4. **Auto-populates the engagement's `skills` block** — reads the staged yaml and extracts `{tools, concepts, categories}` (from `technologies.direct|ecosystem|evaluated`, `approach.frameworks_referenced|design_patterns`, `keywords.methodologies`, and `technologies.categories`) unless the payload's engagement dict already carries a `skills` key. This is the canonical read path for resume-enhancer — the timeline is the single source of truth for skills queries.
5. **Backs up** the current timeline to `career_timeline.json.bak-<timestamp>`.
6. **Rewrites the timeline** atomically, merging the new engagement entry (with the `skills` block embedded) into the specified tenure. If a matching engagement already exists (by `id` or by `name + start month`), it's updated in place — the script is idempotent.

Always run the script with `--dry-run` first to validate the payload and confirm the engagement match decision before committing for real.

**Failure semantics — understand these before using it:**

- Exit 2: preflight failure. Nothing touched. Fix the payload and retry.
- Exit 3: letter or yaml write failed. Nothing touched the timeline. Any `.tmp` files are cleaned up.
- Exit 4: letter + yaml committed, but timeline write failed. The letter and yaml are on disk and valid. **Re-run the exact same commit** — the script is idempotent, and the re-run will heal the timeline.
- Exit 0: everything succeeded. The JSON output lists the backup path so the user can roll back manually if they ever need to.

After a successful commit, tell the user:

- Where the letter and yaml landed (exact paths)
- Which tenure entry it was added to or updated
- The timeline backup path (in case they want to revert)

If the commit fails with exit 4, surface this clearly to the user and offer to re-run the commit with the same payload to heal the partial state. Don't try to fix it by hand.

---

## Iteration

After the successful commit, ask:

- "Does this accurately capture your experience?"
- "Any sections that need more detail or correction?"
- "Anything I missed that you'd want a future resume to highlight?"

Make edits based on feedback. For re-saves, **rebuild the payload and re-run `commit_capture.py`** — never hand-edit the timeline or hand-copy files. The script's match-key lookup will update the existing engagement in place and write a fresh timeline backup each time, so the edit history lives in the backup files if the user ever needs to audit.
