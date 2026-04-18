---
name: resume-enhancer-v2
description: "Transforms an existing resume into a polished, modern .docx document tailored to a specific job description, then runs two post-generation review passes (technical/logical accuracy + recruiter/interviewer review with web-found benchmarks) before shipping. Use this skill whenever the user wants to improve, reformat, rewrite, or tailor their resume or CV with a higher-quality bar than the base resume-enhancer. Triggers include: uploading a resume file and asking to improve it, mentioning 'resume', 'CV', 'job application', 'tailor my resume', 'rewrite my resume', or asking to match a resume to a job posting — when the user wants AI review passes before shipping. This skill handles .docx, .pdf, .txt, and .md resume inputs and always produces a .docx output. If the user says 'help with my resume', 'update my CV for this role', or 'review my resume', use this skill."
---

# Resume Enhancer v2

Transform an existing resume into a professionally formatted, job-tailored .docx document with a modern, executive-grade design — enriched by supplementary experience documents, and validated through two independent review passes (technical/logical accuracy and recruiter/interviewer judgment) before shipping.

## Overview

This skill takes a job description as the primary input, picks the best-fit base resume from the user's role-organized `Resumes/` library (with upload as a fallback), merges in supplementary experience documents, produces a polished .docx resume, and then runs two post-generation review passes to catch issues before delivery:
- Preserves the person's real experience and qualifications (never fabricates)
- Starts from a base resume already calibrated to the target role level (CISO / Director / EM / Principal & Staff / IC), reducing how much needs to be rewritten
- Draws from supplementary experience documents to express achievements more powerfully
- Tailors language, keywords, and emphasis to the target role
- Uses a modern, minimalist executive design (navy accent, letter-spaced name, clean hierarchy)
- Auto-detects and preserves the base resume's section structure
- Outputs a valid, well-formatted .docx file using the bundled template script
- **NEW in v2 — Step 6:** independent technical/logical review of the generated resume by a fresh-context subagent, against a five-item rubric (anchor traceability, date/tech-era plausibility, claim credibility, narrative coherence, logical feasibility). Findings surface as proposed edits; user approves per-edit before regeneration.
- **NEW in v2 — Step 7:** recruiter/interviewer review by three fresh-context subagent personas (Recruiter, Hiring Manager, Interviewer), benchmarked against 2-3 web-found sample resumes for the target role. Findings surface as proposed edits; user approves per-edit before final delivery.

## Workflow

### Step 1: Gather the Job Description

The JD is the primary input — it drives everything downstream, including which base resume to start from. Ask the user for the full JD text (or a link to it). If they don't have a specific JD, ask what type of role they're targeting (title, industry, level, key skills) so you can still route the library pick and tailor the language.

Read the JD carefully before moving on. You'll use it again in Step 1.1 to pick a base resume, and in Step 2 to plan the tailoring.

### Step 1.1: Auto-select the base resume from the user's library

Before any analysis or enhancement, pick a base resume from the user's library at `<workspace>/Resumes/`. The library already contains role-tailored resumes — starting from the right base dramatically reduces how much the skill has to rewrite.

**Finding the workspace:** The workspace is the folder the user has selected (in Cowork) or the current working directory context. Look for a directory containing a `Resumes/` subfolder; if you're not sure where it lives, ask the user for the path rather than guessing. If no `Resumes/` folder exists, skip straight to Step 1.1d (user-uploaded base).

The library is organized into five role folders (plus an `Archive/` folder you should ignore):

- `Resumes/CISO & Executive/` — CISO, Chief Security Officer, VP of Security, Head of Security at C-suite scope (reports to CEO/CIO, owns security strategy for the org)
- `Resumes/Director/` — Director of Security Engineering, Sr. Director, Head of [AppSec/Cloud Security/etc.] leading managers beneath them
- `Resumes/Engineering Manager/` — Engineering Manager, Security Engineering Manager, Team Lead with direct reports and a team to grow
- `Resumes/Principal & Staff/` — Staff, Principal, Distinguished engineer/architect — senior IC influence at org scope without formal people management
- `Resumes/Technical IC/` — Security Engineer, Senior Security Engineer, Software Engineer (Security) — IC below Staff level

#### Step 1.1a — Pick the role folder (hybrid keyword rules + LLM judgment)

Use two passes. Keyword signals give you a fast first guess; then re-read the JD with theory of mind to confirm or override.

**Pass 1 — keyword signals in the JD title and summary:**

| Signals in JD | Route to |
|---|---|
| "CISO", "Chief Security Officer", "VP of Security", "Head of Security" reporting to CEO/CIO | `CISO & Executive` |
| "Director", "Sr. Director", "Head of [domain]" leading managers/directors | `Director` |
| "Manager", "Engineering Manager", "EM", "Team Lead" with direct reports | `Engineering Manager` |
| "Staff", "Principal", "Distinguished", "Lead Architect" (senior IC, not people manager) | `Principal & Staff` |
| "Security Engineer", "Senior Security Engineer", "Software Engineer — Security" | `Technical IC` |

**Pass 2 — LLM judgment on scope and intent:**

Titles mislead. A "Senior Security Engineer" role at a small startup may expect Staff-level scope; a "Principal" at one company may be IC while at another it's senior manager. Re-read the JD and weigh:

- Does the JD mention **managing people, budget, or headcount**? Lean Manager / Director / CISO.
- Does it emphasize **technical depth and cross-org influence without direct reports**? Lean Staff / Principal.
- Is the scope **strategic** (board briefings, risk committee, owning security program for the whole org)? Lean CISO.
- Is the scope **functional** (owning a specific security domain end-to-end, leading a team of 5-15)? Lean Director or EM depending on org size.
- Is the scope **hands-on delivery** (writing code, responding to incidents, building features)? Lean IC tiers.

If Pass 1 and Pass 2 disagree, **prefer Pass 2** and note the reason when you present the pick to the user.

**Worked examples:**

*Example A — clean Engineering Manager match.* JD: "Engineering Manager, Cloud Security at [public SaaS company]. Lead a team of 6 engineers. Drive quarterly security roadmap. Partner with product and SRE."
→ Pass 1: `Engineering Manager` (keyword "Engineering Manager" + team-of-6).
→ Pass 2: confirms — team management + roadmap ownership at team scope.
→ **Pick: `Engineering Manager/`.**

*Example B — ambiguous Principal vs Director.* JD: "Principal Security Engineer at [15-person startup]. Own the security org. Hire and mentor. Own the security budget. Report to the CTO."
→ Pass 1: `Principal & Staff` (keyword "Principal").
→ Pass 2: disagrees — hiring authority, budget ownership, and "own the security org" read as Director-level scope at a small org that doesn't yet have formal titles.
→ **Present both options to the user:** "The title says Principal but the scope (owns the security org, hires, owns budget) reads like a Director role at a mid-sized company would. Should I start from `Principal & Staff/` or `Director/`?"

*Example C — Head of X under a CISO.* JD: "Head of Application Security at [Fortune 500 bank]. Report to CISO. Lead 15 engineers across 3 teams. Own AppSec strategy."
→ Pass 1: ambiguous — "Head of" could be either.
→ Pass 2: reports to a CISO and leads managers → Director-level inside a larger security org.
→ **Pick: `Director/`** (explain the reasoning to the user when presenting the pick).

*Example D — clean Technical IC.* JD: "Senior Security Engineer at [mid-size tech]. Write detection rules. Respond to incidents. Contribute to the security platform. Individual contributor."
→ Pass 1: `Technical IC` (keyword "Senior Security Engineer" + "individual contributor").
→ Pass 2: confirms — hands-on delivery, no leadership scope mentioned.
→ **Pick: `Technical IC/`.**

*Example E — CISO.* JD: "VP & CISO at [growth-stage fintech]. Report to CEO. Own security and compliance programs firm-wide. Brief the board quarterly."
→ Pass 1: `CISO & Executive` (keyword VP + CISO + reports-to-CEO).
→ Pass 2: confirms — board-level visibility, firm-wide scope.
→ **Pick: `CISO & Executive/`.**

#### Step 1.1b — Pick the best-fit resume WITHIN the chosen folder

Once the folder is chosen, list every `.docx` and `.pdf` file in it. **Read each file's contents** — don't rely on filename alone. Some filenames carry company tags (e.g., `Candidate -Director - Security-Nvidia.pdf`) or format hints (e.g., `_Concise`, `_Extensive`), but the actual framing and emphasis live in the file contents.

How to read each format (fall back to the next option if a tool isn't installed — don't give up on a resume just because one extraction method fails):

- **.pdf**: try `pdftotext -layout <file> -`; if not installed, use the bundled `pdf` skill (see `/mnt/skills/public/pdf/SKILL.md` or the installed pdf skill), or `pip install pdftotext --break-system-packages`
- **.docx**: try `pandoc <file> -t plain`; if not installed, use python-docx (`python3 -c "import docx; d=docx.Document('<file>'); print('\n'.join(p.text for p in d.paragraphs))"`) or the bundled `docx` skill

If a folder has 0 files (empty or all files failed to read), fall through to Step 1.1d. If a folder has exactly 1 file, pick it and move on — no need to rank a single item.

For each candidate resume, score fit against the JD on four dimensions. You're looking for the resume that will need the least rewriting to align with the JD:

1. **Domain alignment** — Does the JD emphasize AI security, cloud security, AppSec, SOC/IR, data security, product security, etc.? Pick the resume that already emphasizes the same domain. A resume centered on detection engineering is a rough base for a cloud security architect JD.
2. **Scale and context** — Enterprise vs. startup, team size, multi-org coordination, regulated industry (finance/healthcare) vs. consumer tech. Pick the resume whose framing matches the JD's scale so you don't have to invent new context.
3. **Technology overlap** — Count the concrete tech terms the JD calls out (AWS/Azure/GCP, specific tools like Wiz/Splunk/Kubernetes, specific frameworks like NIST CSF, MITRE ATT&CK, OWASP Top 10). Pick the resume with the most overlap already present.
4. **Length/depth calibration** — Concise vs. extensive variants. FAANG-style postings often get skimmed (favor concise); consulting or executive briefings get read (favor extensive). Match the format the JD's hiring manager will likely prefer.

*Scoring note:* you don't need a numeric rubric — a quick LLM judgment on each dimension is enough. What matters is explicit reasoning you can show the user.

#### Step 1.1c — Present top picks and confirm with user (unless the match is obvious)

When the best candidate is clearly ahead of the alternatives, pick it and move on — but still tell the user what you picked and why in one sentence. When two or three resumes are close, **stop and present the top picks with reasoning** before proceeding.

Format:

> I found three candidates in `Resumes/Engineering Manager/` that fit this JD:
>
> 1. **Candidate -Engineering Manager - Security & AI_Concise.docx** — strongest match: already emphasizes AI security + leadership; concise format fits the FAANG EM posting's skim-first style.
> 2. **Candidate -Engineering Manager - Attack Surface Management.pdf** — close second on cloud security breadth, but weaker on the AI angle this JD emphasizes.
> 3. **Candidate -Engineering Manager - Security Consulting.docx** — good leadership framing, but consulting framing may not fit an in-house EM role.
>
> I'd use #1 as the base. Proceed, or use a different one?

If exactly one resume fits (e.g., the JD names a specific company you already have a tagged resume for, or only one resume covers the required domain), proceed and tell the user what you picked in one sentence — no need to belabor the choice.

#### Step 1.1d — Fallback: user-uploaded base resume

If the user uploads their own resume (supported formats: .docx, .pdf, .txt, .md) instead of or alongside a library pick, honor that — use the uploaded file as the base and skip the library scan. In your summary to the user, mention whether you used their upload or a library pick so there's no ambiguity about the source.

Supported format handling for user uploads:
- **.docx**: pandoc or python-docx to extract text
- **.pdf**: pdftotext or the pdf skill
- **.txt, .md**: read directly

### Step 1.2: Gather supplementary experience documents

Ask if the user has additional files that describe their experience in more depth — STAR method stories, interview prep notes, project writeups, career progression documents, achievement lists, performance reviews, experience letters from the `experience-letter` skill, etc. These are gold: they contain authentic details and context that make resume bullet points genuinely compelling instead of generic.

If the workspace has an `Experience/` folder or a `career_timeline.json`, offer to scan those too — they're often the richest source of concrete metrics and stories.

Read all provided supplementary files and index the key achievements, metrics, and stories they contain. You'll draw from this index in Step 2.

### Step 2: Analyze and Plan

Before writing anything, do this analysis carefully. This is the most important step — it determines how good the final resume will be.

**`career_timeline.json` is the single source of truth for all resume data** — contact info, company names, roles, dates, skills, certifications, and education all come from there. The base resume selected in Step 1.1 is a format reference only: use it to gauge the expected output length (1 page vs. 2) and confirm which sections suit this role tier. Do not extract data from it.

`career_timeline.json` provides:
- `candidate.*` — name, email, phone, LinkedIn, GitHub, location
- `tenures[]` — employers, role titles, employment dates
- `tenures[].engagements[]` — individual projects with roles, dates, and per-engagement `skills.tools / concepts / categories`
- `open_source[]` — open-source projects with the same skills structure
- `education[]` and `certifications[]`
- `yaml_path` per engagement — pointer to the detailed experience letter (read only in Step 2E, for confirmed engagements)
- `_gap` marker — flags engagements with no experience letter yet (lower-confidence evidence)

This step runs as five sub-phases. Do not skip to bullet writing until Step 2E — the earlier phases are what make the bullets accurate and defensible.

#### Step 2A — JD Skill Decomposition

Parse the JD into a structured skill inventory with priority tags. You'll use this as the query set for the evidence search in Step 2C.

```json
{
  "required": ["Cloud Security (AWS/GCP)", "CSPM", "Security Program Leadership"],
  "preferred": ["AI Security", "DevSecOps", "NIST CSF"],
  "leadership": ["Team management 5+", "Executive communication", "Cross-functional influence"],
  "domain": ["Financial services", "SaaS"]
}
```

Required skills drive the mapping. Preferred/leadership/domain skills provide secondary weighting. Extract these from the JD's "Requirements," "Must-have," "Nice-to-have," and "About the role" sections. When the JD uses vague language, decompose it: "strong security background" → specific skills based on the rest of the JD.

#### Step 2B — Experience Corpus Indexing

`career_timeline.json` is the source of truth and the primary matching corpus — read it once, do not open individual YAML files at this stage.

For each engagement in `tenures[].engagements[]` and `open_source[]`, build an index entry from fields that are already present in the timeline:

- `engagement_id`, `name`, `organization` (parent tenure's `employer`), `role_in_engagement`, `start`, `end`
- `skills.tools` — hands-on tools the user worked with directly (highest-signal match surface)
- `skills.concepts` — frameworks, patterns, methodologies, domain knowledge
- `skills.categories` — domain/capability buckets (broadest match surface; useful for catching JD skills expressed at category level)
- `yaml_path` — retain as a pointer; you'll use it later in Step 2E to fetch impact text and anchor IDs for confirmed engagements only
- `_gap` — if present, this engagement has no experience letter and limited evidence; flag it as lower confidence

The flat union of `tools + concepts + categories` per engagement is the matching surface for Step 2C. You do not need to open YAML files to do the skill mapping.

**Fallback:** If `career_timeline.json` doesn't exist in the workspace, fall back to reading whichever supplementary documents the user provided in Step 1.2 as unstructured text. Mark all evidence in that case as `alignment_type: inferred` and note to the user that a structured `career_timeline.json` (maintained by the `experience-letter-v2` skill) would make this step more precise.

**Engagements with `_gap`:** Treat these as partial evidence — the timeline entry exists but no YAML/letter was written. You can use them to confirm a skill was exercised, but you cannot cite an anchor ID or pull a specific impact metric. Flag them as `alignment_type: partial` and `use_as: research_needed` in the mapping.

#### Step 2C — JD-Skill to Evidence Mapping

For each skill from the Step 2A inventory, scan the Step 2B index and produce a mapping entry. Match against the `tools + concepts + categories` union per engagement. Use exact/substring match first, then LLM judgment for terminology differences (e.g., the JD says "AI Security" and the timeline has `"Agentic AI Security"` in categories — that's a direct match even though the labels differ).

Structure each mapping entry as:

```json
{
  "jd_skill": "CSPM",
  "jd_priority": "required",
  "evidence": [
    {
      "engagement_id": "cspm-transformation",
      "yaml_path": "Experience/Security Engineer (2021-Current)/cspm-transformation.yaml",
      "matched_on": ["CSPM (Cloud Security Posture Management)", "Cloud Governance"],
      "alignment_type": "direct",
      "use_as": "verbatim",
      "anchor_id": null
    }
  ],
  "gap": false
}
```

`anchor_id` is `null` at this stage — it gets filled in Step 2E when you read the YAML for confirmed engagements. Don't open YAML files yet.

**Alignment types:**
- `direct` — the JD skill matches an item in `skills.tools`, `skills.concepts`, or `skills.categories` directly or by close paraphrase
- `inferred` — the engagement clearly involves this skill (via LLM judgment on the work context) but the timeline's skill fields don't use the JD's terminology; requires user confirmation before use
- `partial` — the engagement has `_gap` (no YAML/letter) or only tangentially covers the skill; lower confidence

**Use-as tags:**
- `verbatim` — direct match; pull impact text from the YAML anchor in Step 2E with minimal rewording
- `enhance` — authentic experience exists but framing needs updating to mirror JD language or surface impact more clearly
- `research_needed` — match found but the engagement has `_gap` or is `inferred`; prompt user before including

**Gap entry (no match found across all engagements):**
```json
{
  "jd_skill": "Kubernetes Security",
  "jd_priority": "required",
  "evidence": [],
  "gap": true
}
```

When finished, save the complete mapping to `skill_evidence_map.json` in the workspace. This is the persistent output of Step 2 — confirmed entries in this file are what Step 2E uses to select which YAMLs to open and which anchor IDs to pull.

#### Step 2D — Confirmation Loop (Batched by Alignment Type)

Present the mapping to the user, batched by alignment type to minimize interruptions. Work through required skills first, then preferred/leadership/domain.

**Direct evidence (verbatim or enhance):** Announce and proceed — no confirmation needed.
> "Found direct evidence for 5 of 8 required skills across 4 engagements. Proceeding with those."

**Inferred evidence:** Present each case and confirm before using:
> "For 'AI Security' (preferred): In the `ml-pipeline-security` engagement, you threat-modeled ML training pipelines for data poisoning and model exfiltration risks. The YAML doesn't use the label 'AI Security' but this is precisely what the JD means by it. Should I frame this as AI Security experience?"

When presenting an inferred mapping, always include: the JD skill it supports, the engagement it comes from, a one-sentence summary of the evidence, and your reasoning for the inference. Keep it concise — the user is confirming a judgment call, not re-reading the full letter.

**Gaps:** Report each gap explicitly and offer options. Don't silently skip required-skill gaps.
> "No evidence found for 'Kubernetes Security' (required). Three options: (1) skip this skill and leave it unaddressed, (2) tell me about relevant experience and I'll draft a bullet from what you share, (3) there may be an engagement not yet captured as a letter — would you like to run the experience-letter-v2 skill first and come back?"

Collect all responses before moving to Step 2E. Don't begin bullet drafting until the full confirmation loop is resolved.

#### Step 2E — YAML Read + Bullet Plan (Confirmed Engagements Only)

Only after Step 2D is fully resolved, open the YAML files — but only for engagements that appear in confirmed (non-gap) mapping entries. This is the first and only point where you read individual YAML files.

For each confirmed engagement's `yaml_path`:
1. Read the YAML and locate the relevant `impact.quantitative[]`, `approach.frameworks_referenced`, `leadership.activities[]`, and `proudest_achievement` sections
2. Find the specific anchor ID for the claim you intend to use (e.g., `cspm-transformation.impact.quantitative.attack-surface`)
3. Update `anchor_id` in `skill_evidence_map.json` from `null` to the resolved value
4. Extract the exact evidence text from that anchor

Then draft bullet candidates:

- For `verbatim` entries: minimal rewording, preserve the original metric exactly as it appears in the YAML (including confidence qualifiers like "~30-40% projected")
- For `enhance` entries: keep the core fact accurate, update framing to mirror the JD's terminology and surface the impact using the STAR pattern (strong verb + what you did + measurable result)
- Apply seniority-appropriate framing from Step 1.1: IC bullets emphasize delivery and hands-on work; Director/CISO bullets emphasize program ownership and org-level outcomes
- For `research_needed` entries the user confirmed: draft from what the user provided in Step 2D, not from the YAML.

**Bullet writing rules — apply while drafting:**

*Active voice and strong verbs.* Every impact bullet leads with an action verb in active voice that asserts what you did. Weak linkers and passive framings get rewritten before the bullet leaves this step. Scan for the banned phrases below and replace them.

| Banned phrase | Replace with |
|---|---|
| "mapped to" | mitigates, enforces, satisfies, addresses |
| "aligned with" | enforces, complies with, mitigates |
| "responsible for" | owns, drives, delivers |
| "worked on" | built, shipped, designed, delivered |
| "involved in" | led, drove, contributed to |
| "assisted with" | built, delivered (or drop if not your core work) |
| "helped with" | built, delivered (or drop) |
| "participated in" | led, drove, contributed to |

Preferred verbs (pick whichever fits the action): *mitigates, enforces, reduces, blocks, eliminates, prevents, drives, owns, delivers, ships, builds, designs, scales, accelerates, automates, hardens, decomposes, instruments.*

*Role-tier metric filter.* The base resume tier from Step 1.1 (Technical IC / Principal & Staff / EM / Director / CISO) gates which classes of metrics are credible. Asserting a metric the role tier can't plausibly own makes the bullet read as inflated and triggers reviewer skepticism. Apply this matrix:

| Metric class | Technical IC | Principal & Staff | EM | Director | CISO |
|---|---|---|---|---|---|
| Revenue / P&L / ARR attribution | block | block | block | cost-savings only | allow |
| Headcount ("led team of N", "managed N") | block | "mentored N" only | allow | allow | allow |
| Budget ownership ("owned $X budget") | block | "influenced $X spend" only | allow | allow | allow |
| Org-wide / firm-wide / company-wide scope | block | "across N teams" only | "across team" | allow | allow |

If the YAML evidence contains a metric the role tier blocks, reframe to a credible substitute — e.g., "owned $2M security budget" on a Technical IC bullet becomes "drove tool selection that reduced licensing spend ~30%." When no credible substitute exists, drop the metric rather than misattribute it.

#### Step 2F — Bullet QA Gate (Run Before Writing the .docx)

After all bullets are drafted in Step 2E, run an explicit QA pass over every bullet you intend to ship. This is a hard gate: any bullet that fails one of these checks must be rewritten or dropped — do not proceed to the .docx step until the gate is clean.

For each bullet, verify all four checks:

1. **Active voice and strong verb.** First action word in the bullet is an action verb in active voice. Scan for every phrase in the banned list from Step 2E. If any banned phrase appears, rewrite using a preferred verb. No bullet ships with "mapped to", "aligned with", "responsible for", "worked on", "involved in", "assisted with", "helped with", or "participated in".

2. **Role-tier metric fit.** Identify each metric in the bullet (revenue, headcount, budget, scope). Check it against the role-tier matrix in Step 2E. If the bullet asserts a metric the tier blocks, reframe to a credible substitute or remove the metric. Revenue / P&L / ARR claims on Technical IC, Principal & Staff, or EM bullets are auto-fail and must be rewritten.

3. **Evidence anchor present.** The bullet traces back to a confirmed `anchor_id` from Step 2E — or to a user-provided narrative for `research_needed` entries. Bullets without provenance are auto-fail; do not invent or compose claims that don't trace to an anchor or a user-confirmed source.

4. **Single concrete impact.** The bullet expresses one action and one measurable outcome (action + result). Compound bullets that chain three or more claims read as filler — split into separate bullets or trim to the strongest claim.

5. **Link verification (HTTP health + LLM content match).** Every URL that will appear in the resume must be verified before the .docx is written. This covers contact links (LinkedIn, GitHub, portfolio, personal site) and any URLs embedded inside bullets or project references. Run the two-stage check below for each URL.

   *Stage 1 — HTTP health.* Fetch the URL via the `WebFetch` tool. Reject any non-2xx response. For 3xx redirects, follow to final destination and pass only if the final host still matches the expected domain family (e.g., `linkedin.com` → `linkedin.com` is fine; `linkedin.com` → a squatter domain is a fail). Network errors and rate-limit responses are treated as inconclusive and surfaced to the user the same way as a verification failure — do not silently skip.

   *Stage 2 — LLM content match.* For URLs that pass stage 1, pass the fetched page content to an LLM together with a one-sentence expectation derived from the link type. The LLM returns a pass/fail decision plus a confidence score on [0.0, 1.0]. Pass threshold is ≥ 0.7; anything below is treated as failed.

   Expectations by link type:

   | Link type | Expectation to evaluate against |
   |---|---|
   | LinkedIn profile | Candidate's LinkedIn profile — name, headline, and current role consistent with `candidate.*` in `career_timeline.json` |
   | GitHub profile | Candidate's GitHub profile — username matches, profile appears active (not a stub/placeholder account) |
   | Portfolio / personal site | Candidate's personal site — name present, role framing consistent with the resume |
   | Project reference (inside a bullet) | Page delivers the specific artifact the bullet claims (repo, demo, writeup, paper, talk) — LLM judges whether content matches the bullet's assertion |

   *On failure — prompt the user for the corrected URL.* Do not auto-fix, do not silently drop, and do not ship a failed link unconfirmed. Surface the failure with diagnostic context and ask for the right URL. Format:

   > "Link verification failed for GitHub URL `https://github.com/candidate-profile-old`. HTTP 200, but the profile shows 0 repos, last activity 2018, and the display name doesn't match. Expected: your current GitHub profile. What's the correct URL? (Or type `remove` to drop the link, or `keep` to ship as-is with a flag in the QA summary.)"

   Collect the corrected URL, re-run both stages, and only mark the check as passed once a URL clears both. Links the user marks `remove` are stripped from the resume. Links marked `keep` are shipped unchanged but flagged in the QA summary so the user has a paper trail.

Report the QA outcome to the user as a one-line summary before writing the .docx, e.g.: "QA pass: 14 bullets reviewed, 3 reworded for active voice, 1 metric reframed (team-size on a Principal & Staff bullet), 5 links verified (4 pass, 1 corrected via prompt), 0 dropped." Then proceed to Step 3.

### Step 3: Build the Resume JSON

This skill includes a bundled template script at `scripts/generate_resume.js` that produces a professionally designed .docx with a modern executive layout. Your job is to prepare the data — the script handles the design.

**Data sourcing — where each JSON field comes from:**

| JSON field | Source |
|---|---|
| `name` | `career_timeline.json` → `candidate.name` |
| `contact.email` | `career_timeline.json` → `candidate.email` |
| `contact.phone` | `career_timeline.json` → `candidate.phone` |
| `contact.linkedin` | `career_timeline.json` → `candidate.linkedin` |
| `contact.location` | `career_timeline.json` → `candidate.location` |
| `contact.github` | `career_timeline.json` → `candidate.github` — include for Technical IC and Principal & Staff tiers only; omit for Director and above |
| `summary` | You write this — synthesize JD requirements + top confirmed evidence from Step 2. Always include. Tone varies by tier — see section ordering below |
| `experience[].company` | `career_timeline.json` → tenure `employer` |
| `experience[].role` | `career_timeline.json` → engagement `role_in_engagement` |
| `experience[].dates` | `career_timeline.json` → engagement `start` / `end` formatted as `"MMM YYYY – MMM YYYY"` or `"MMM YYYY – Present"` |
| `experience[].bullets` | Step 2E bullet candidates — sourced from YAML anchors, confirmed in Step 2D, QA-gated in Step 2F |
| `skills.groups` | JD-aligned skills from Step 2C confirmed map; group by category |
| `education[].institution` | `career_timeline.json` → `education[].institution` |
| `education[].degree` | `career_timeline.json` → `education[].degree` |
| `education[].dates` | `career_timeline.json` → `education[].year` (single graduation year, e.g. `"2017"` — not a range) |
| `education[].details` | Optional — thesis title, honors, or relevant coursework; omit if not applicable |
| `certifications[]` | `career_timeline.json` → `certifications[]` |
| Open-source projects | `career_timeline.json` → `open_source[]` — include as a `"list"` section titled "Open Source / Side Projects" for Technical IC and Principal & Staff tiers; omit for Director and above unless the JD specifically values it |

**How `summary` is rendered by the script:** The script renders `summary` as a fixed "Professional Summary" section before all entries in `sections[]`. It is not part of the `sections` array — it is a separate top-level field. Section ordering below controls only the order of items within `sections[]`.

Structure your content as a JSON file with this schema:

```json
{
  "name": "Full Name",
  "contact": {
    "email": "email@example.com",
    "phone": "+1 555 123 4567",
    "linkedin": "linkedin.com/in/username",
    "location": "City, State",
    "github": "github.com/username"
  },
  "summary": "2-3 sentences tailored to the target role. Tone varies by tier — technical depth and specific technologies for IC, scope and program ownership for Director and above. Always include.",
  "sections": [
    {
      "type": "experience",
      "title": "Professional Experience",
      "entries": [
        {
          "company": "Company Name",
          "role": "Job Title",
          "dates": "Jan 2022 – Present",
          "bullets": [
            "Strong action verb + what you did + measurable result",
            "3-5 bullets per role, most impactful first"
          ]
        }
      ]
    },
    {
      "type": "skills",
      "title": "Technical Skills",
      "groups": [
        { "category": "Category Name", "items": "Skill 1, Skill 2, Skill 3" }
      ]
    },
    {
      "type": "education",
      "title": "Education",
      "entries": [
        {
          "institution": "University Name",
          "degree": "Degree Title",
          "dates": "2017",
          "details": "Optional: thesis, honors, relevant coursework"
        }
      ]
    },
    {
      "type": "certifications",
      "title": "Certifications",
      "items": ["Cert 1", "Cert 2"]
    },
    {
      "type": "list",
      "title": "Open Source / Side Projects",
      "items": ["Project Name — one-line description and impact"]
    }
  ]
}
```

**Section ordering guidance — matched to the library's five-tier ladder:**

Note: `summary` is always rendered before `sections[]` by the script. The ordering below refers to entries within `sections[]` only.

- **Technical IC**: Skills → Experience → Open Source → Education → Certifications. Summary is technical in tone — lead with specific domain and years of hands-on experience, name key technologies or specializations, end with what the candidate builds or defends. Avoid leadership or program language. Include `contact.github`. Bullets emphasize hands-on delivery (built, shipped, detected, automated).
- **Principal & Staff**: Experience → Skills → Open Source → Certifications → Education. Summary leads with years of senior-IC scope and a signature technical bet. Include `contact.github`. Bullets emphasize cross-org influence, architecture, and decisions only a senior IC would own.
- **Engineering Manager**: Experience → Skills → Certifications → Education. Summary leads with team-building and delivery metrics. Bullets balance people outcomes (team growth, retention, hiring) with technical program delivery. Omit open-source section unless directly relevant to the JD. Omit `contact.github`.
- **Director**: Experience → Skills → Certifications → Education. Summary is strategic — scope of org, program ownership, business impact. Bullets emphasize org-level results (program launched, cross-functional wins, budget managed). Omit open-source section and `contact.github`.
- **CISO & Executive**: Experience → Skills → Certifications → Education. Summary reads like an exec bio — scope, board visibility, regulatory posture, signature programs. Bullets emphasize firm-wide outcomes, regulatory/compliance, board-level influence. De-emphasize tools and tech; emphasize programs, frameworks, and risk posture. Omit open-source section and `contact.github`.

**Bullet point writing rules:**

The detailed rules for verb choice, active-voice enforcement, and role-tier metric filtering are defined in Step 2E and enforced as gates in Step 2F. Quick reference:

- Start every bullet with a strong action verb. Banned weak phrases and the full preferred-verb palette live in Step 2E.
- Include a measurable outcome whenever possible — but only metric classes that fit the role tier per the Step 2E matrix.
- Front-load the most impressive/relevant achievements for each role.
- 3-5 bullets per role. More recent roles get more bullets.
- Keep bullets to 1-2 lines each — concise and scannable.
- Match the JD's language where the experience genuinely supports it.

### Step 4: Generate the .docx

First, install the docx package if needed:
```bash
npm install docx
```

Then run the template script (the path is relative to this skill's directory):
```bash
node <skill-path>/scripts/generate_resume.js <input.json> <output.docx>
```

The script produces a document with:
- **Deep navy accent** (#1B3A5C) — authoritative, executive feel
- **Letter-spaced centered name** — immediately draws the eye
- **Contact bar** with pipe separators, centered below the name
- **ALL-CAPS section headers** with subtle underline dividers
- **Role + Company + Date** format with right-aligned italic dates
- **Colored bullet points** for visual rhythm
- **Categorized skills** with bold category labels
- **Compact certifications** as inline bullet-separated text
- **Clean education** entries with right-aligned dates
- ATS-compatible single-column layout
- US Letter size with optimized margins (0.75" sides, 0.5" top/bottom)

### Step 5: Validate and Save Draft

After generating the .docx:
1. Validate it: `python <docx-skill-path>/scripts/office/validate.py output.docx`
2. Verify all dates, company names, and credentials match the original resume exactly
3. Confirm details from experience docs are attributed to the correct role/company
4. Check it fits within 1-2 pages (1 page for most, 2 for 15+ year careers)
5. Save the DRAFT .docx to the user's workspace folder with a clear filename like `Resume_[Name]_[TargetRole].docx`. Steps 6 and 7 may regenerate this file in place after review passes — the filename stays the same, the content updates. Do not present the file as final until Steps 6 and 7 complete.

### Step 6: Technical & Logical Review (Independent Subagent)

After the draft .docx is saved in Step 5, run an independent technical and logical review. The drafting LLM gave the resume every benefit of the doubt while writing it — a fresh-context subagent with no stake in the drafting decisions will catch credibility issues the writer missed.

**Mechanics — spawn a subagent with the `Agent` tool:**

- `subagent_type`: `general-purpose`
- `description`: "Technical accuracy review of generated resume"
- Prompt contents: the resume JSON from Step 3 (NOT the .docx — JSON is cleaner for LLM parsing), the target JD, and the relevant subset of `career_timeline.json` (tenures + engagements referenced in the resume, including `yaml_path` pointers). Instruct the subagent to run the five-item rubric below and return structured findings as JSON.

**Rubric — five independent checks:**

1. **Anchor traceability.** For every bullet in the resume's Experience section, identify which engagement in `career_timeline.json` it traces back to. Match on company, dates, and content. Any bullet that doesn't map cleanly to an engagement is an unsourced claim — flag as HIGH severity.

2. **Date & tech-era plausibility.** Flag anachronisms (e.g., Kubernetes GA'd June 2015 — claiming K8s experience in 2013 is a fail; Terraform 0.1 was July 2014; Docker was March 2013; AWS Lambda was November 2014). Flag role dates that overlap or contradict the timeline. Flag unexplained gaps the resume doesn't address.

3. **Claim credibility (scope + metrics).** Belt-and-suspenders re-check of Step 2F on the final assembled resume — verify role-tier fit on every bullet. Check metrics add up internally (team grew 5→8 = 60%, not 300%). Flag percentages without a baseline. Flag metrics that contradict the engagement YAML's `impact.quantitative` section.

4. **Narrative / progression coherence.** Read the resume top to bottom as a story. Flag: senior→junior moves without context, duplicate achievements appearing under multiple roles, tech stack that doesn't connect between adjacent roles, summary that contradicts the bullets, missing years.

5. **Technical / logical feasibility.** Is each claim physically and causally plausible? Red flags: "reduced cost 100% while scaling 10x" (causal impossibility), "led a 500-person team as an IC" (role-type impossibility), "shipped in 2 weeks" for scope that clearly required more (scope impossibility), claims that chain multiple impressive metrics in a single bullet without naming trade-offs.

**Subagent returns structured findings JSON:**

```json
{
  "overall_verdict": "pass" | "needs_changes" | "fail",
  "findings": [
    {
      "rubric_item": "anchor_traceability" | "date_plausibility" | "claim_credibility" | "narrative_coherence" | "logical_feasibility",
      "severity": "HIGH" | "MEDIUM" | "LOW",
      "current_text": "exact bullet or phrase from the resume",
      "issue": "one-sentence description of what's wrong",
      "proposed_edit": "the specific replacement text, OR 'REMOVE' if the claim should be dropped, OR 'NEEDS_USER_INPUT' if the subagent can't judge without more context",
      "rationale": "why the proposed edit fixes the issue"
    }
  ]
}
```

**Gate:**
- Zero HIGH-severity findings → pass the gate; move to Step 7.
- Any HIGH-severity finding → must be resolved before moving on.
- MEDIUM and LOW findings are presented but optional.

**Feedback loop (user-approved per-edit):**

Present all findings to the user in one batch, grouped by severity. For each finding, show: the current text, the issue, the proposed edit, and the rationale. User responds per finding with one of: `accept`, `reject`, `modify: <user-supplied edit>`, or `need more info`.

Apply approved edits to the resume JSON. Re-generate the .docx (Step 4). Re-run Step 6 with the updated resume. **Max 2 iterations.** If HIGH-severity findings persist after two iterations, stop the auto-loop and ship with a summary of unresolved issues flagged for the user's attention. Do not silently paper over unresolved HIGH-severity findings.

Report the Step 6 outcome to the user as a one-line summary: "Step 6 review: 7 findings (2 HIGH, 3 MEDIUM, 2 LOW). 2 HIGH edits accepted, 1 MEDIUM modified, rest skipped. Resume regenerated, re-review clean."

### Step 7: Recruiter & Interviewer Review (Multi-Persona Subagents with Web Benchmarks)

After Step 6 clears the technical/logical gate, run a three-persona review from the perspective of the people who actually read resumes for a living. Benchmark against 2-3 published sample resumes for the same role to ground the review in real-world expectations.

**Phase 7A — Gather benchmark samples from the web.**

Use `WebSearch` with role-targeted queries to find 2-3 published strong-example resumes for the target role. Query templates:
- `"sample resume" "<target role title>" 2025` — current-year examples
- `"strong resume example" "<target domain>" <seniority>` — e.g., `"strong resume example" "security engineering manager" senior`
- `"<company name> resume example"` if the JD names a specific company and you want to match that company's bar

For each promising search result, use `WebFetch` to pull the content. Filter for:
- Must be a resume sample (not a "how to write a resume" article)
- Must be for a role matching the target role's tier (see Step 1.1's five-tier ladder)
- Extract clean resume text — skip heavy branding, ads, sidebars

If fetching fails, returns a generic template, or returns content for the wrong role: fall back gracefully. Tell the user which benchmark fetches succeeded and which did not. Run the persona reviews even with zero benchmarks — they work, just with less grounding.

Target: 2-3 usable benchmark samples. If zero after 5 search attempts, move on and note to the user that Phase 7B ran without external benchmarks. Do not block Step 7 on benchmark availability.

**Phase 7B — Spawn three persona subagents in parallel.**

Use the `Agent` tool three times in a SINGLE message (parallel execution). Each subagent gets fresh context, the generated resume, the target JD, the benchmark samples (if any), and a distinct persona-specific prompt. Personas:

| Persona | Read time | Focus | Deliverable |
|---|---|---|---|
| Recruiter | 30-second skim | Structure, keyword match to JD, scannability, length fit, typos, disqualifying signals | Pass/concern/fail verdict + top 3 concerns + 3 proposed edits |
| Hiring Manager | 2-minute read | Role-fit across seniority and scope, technical depth appropriate to the tier, signals of ownership vs. tourism, deal-breakers | Pass/concern/fail verdict + top 3 concerns + 3 proposed edits |
| Interviewer | 5-minute deep read | Claims needing substantiation, specific technical questions the bullets suggest, inconsistencies a careful reader would catch, generic vs. specific framing | Top 5 interview questions + top 3 weakest claims + 3 proposed edits |

**Each persona subagent returns structured findings JSON:**

```json
{
  "persona": "recruiter" | "hiring_manager" | "interviewer",
  "verdict": "pass" | "concern" | "fail",
  "concerns": [
    { "issue": "...", "evidence": "exact text from resume", "severity": "HIGH" | "MEDIUM" | "LOW" }
  ],
  "proposed_edits": [
    { "current_text": "...", "proposed_text": "...", "rationale": "..." }
  ],
  "interviewer_questions": ["question 1", "question 2", "question 3", "question 4", "question 5"]
}
```

The `interviewer_questions` field is populated only for the Interviewer persona; the other two personas return an empty array.

**Aggregate and present to user:**

Merge findings across all three personas. Deduplicate — same issue flagged by multiple personas becomes a single higher-priority finding. Present to the user as one batch of proposed edits, tagged with which personas flagged each issue (e.g., "Flagged by Recruiter + Hiring Manager: the third bullet under [Role] is vague — 'led initiatives' doesn't anchor to a specific project").

Also surface the Interviewer's top 5 questions separately — these are useful interview-prep material even if the user doesn't accept any edits.

**Gate:**
- All three personas return `pass` → ship the final .docx.
- Any persona returns `fail` → must be resolved before ship.
- `concern` verdicts are presented as proposed edits but do not block ship.

**Feedback loop (user-approved per-edit):**

Same mechanics as Step 6 — present findings as proposed edits, user responds per finding (`accept` / `reject` / `modify: <text>`), apply approved edits, regenerate .docx (Step 4), re-run Step 7. **Max 2 iterations.** After two iterations with remaining `fail` verdicts, stop the loop and ship with a summary of unresolved issues flagged for the user's attention.

Report the final verdict with a one-line summary: "Step 7 review: Recruiter=pass, Hiring Manager=pass, Interviewer=concern (2 edits proposed, 2 accepted). 3 benchmark resumes used. Final .docx at <path>."

### Step 8: Final Delivery

After Step 7 passes (or the iteration cap is hit), confirm the final state of the .docx with the user and present the file with a `computer://` link. Include a concise two-step review summary in the delivery message:

> Your resume is ready. It went through Step 6 (technical review: 2 edits applied) and Step 7 (recruiter/interviewer review: 1 concern resolved, 2 accepted). Interview-prep questions from the Interviewer persona are listed below. [View your resume](computer:///path/to/Resume_X.docx)

## Important Reminders

- **Accuracy is paramount.** The user's career history, education, certifications, and dates must be preserved exactly. Reword for impact, but never change facts.
- **Experience docs enrich, not replace.** Use supplementary documents to add authentic detail and metrics to bullet points. Every detail you add must genuinely belong to the role and company it appears under.
- **Tailoring is not lying.** Emphasize relevant experience, use the JD's terminology where the user genuinely has the skill, and de-emphasize less relevant items — but don't add fake experience.
- **Keep it to 1-2 pages.** Most professionals: 1 page. Senior professionals (10+ years): 2 pages max. Never exceed two unless explicitly asked.
- **Use the template script.** Don't write custom docx generation code — use `scripts/generate_resume.js` to ensure consistent, professional formatting. Your job is the content and the JSON structure.
- **User-approved edits only.** Steps 6 and 7 propose edits; they never silently rewrite your resume. Every change to the resume JSON between iterations must be explicitly accepted, modified, or authored by the user.
- **Iteration cap is a hard limit.** Steps 6 and 7 each allow at most 2 review→edit→regenerate cycles. After the cap, ship with a summary of unresolved findings — don't loop indefinitely.
- **Fresh-context reviewers.** Step 6 uses one independent subagent; Step 7 uses three parallel persona subagents. Never re-use the drafting LLM's context for reviews — that defeats the independence that makes reviews worth running.