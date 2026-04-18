# AI-Powered Resume Builder: Cowork Guide

> **What you'll build:** A two-skill system that captures project experience as structured data, then generates tailored resumes for any job description.
>
> **Who this is for:** Claude Pro/Max users who want a compounding career asset — not a one-off resume.
>
> **Time to build:** ~2–3 hours for the full system.

---

## The Big Idea

Capture experience once (richly, right after a project ends) → query that library whenever you apply. The more you capture, the better every future resume gets.

```
Finish a project
    │
    ▼
Skill 1: Experience Letter Capture
    └─► experience-name.yaml  +  Experience_Letter.docx  (library grows)
                                        │
                              (weeks/months later)
                                        │
                                        ▼
                          Skill 2: Resume Enhancer
                              └─► Tailored .docx resume
```

---

## Folder Structure

```
GitHub-Cowork_ResumeBuilder/
│
├── Skills/
│   ├── experience-letter-v2/       ← Skill 1: capture experience
│   │   ├── SKILL.md
│   │   ├── references/             ← schema template + filled example
│   │   └── scripts/
│   │
│   └── resume-enhancer-v2/        ← Skill 2: generate tailored resumes
│       ├── SKILL.md
│       ├── scripts/                ← generate_resume.js (.docx template engine)
│       └── evals/
│
├── Resumes/                        ← Base resumes by role level
│   ├── CISO & Executive/
│   ├── Director/
│   ├── Engineering Manager/
│   ├── Principal & Staff/
│   └── Technical IC/
│
├── Experience/                     ← Your growing experience library
│   └── Security Engineer (2021-Current)/
│       ├── compass.yaml
│       ├── cspm-transformation.yaml
│       ├── cloud-coe.yaml
│       └── Experience_Letter_*.docx
│
└── career_timeline.json            ← Canonical career registry
```

- **`Skills/`** — write once, refine over time. Full instructions in each `SKILL.md`.
- **`Experience/`** — one `.yaml` + one `.docx` per project. Machine-readable + human-readable.
- **`Resumes/`** — base resumes by level; the Resume Enhancer picks the right starting point.
- **`career_timeline.json`** — canonical source of truth: roles, tenures, skills taxonomy, education, certifications. Skills query this instead of re-reading every YAML each run.

---

## Understanding Skills

A Skill is a folder with a `SKILL.md` file. Claude reads the YAML frontmatter to decide *when* to invoke it, and the markdown body for *how* to execute it. Reference files (templates, examples) in `references/` load on-demand only.

**Installing:** Copy the skill folder into your workspace (Cowork picks it up automatically), or zip and upload via Claude Desktop → Customize → Skills.

---

## Skill 1: Experience Letter Capture

> Full instructions: [Skills/experience-letter-v2/SKILL.md](Skills/experience-letter-v2/SKILL.md)
> Schema: [Skills/experience-letter-v2/references/](Skills/experience-letter-v2/references/)
> Example outputs: [Experience/Security Engineer (2021-Current)/](Experience/Security%20Engineer%20(2021-Current)/)

**Trigger:** `"Capture my experience on [project name]"`

Runs a structured 10-step interview — project context → problem → approach → deliverables → technologies → stakeholders → leadership → impact → proudest achievement → document generation. At each step Claude probes for specifics rather than accepting vague answers.

**Outputs:**
- `experience-name.yaml` — structured, machine-readable, with provenance anchor IDs on every item so resume bullets can be traced back to source evidence
- `Experience_Letter_Name.docx` — polished human-readable document

**Best practice:** Run this immediately after finishing a project while details are fresh. Be specific — rough numbers beat no numbers.

---

## Skill 2: Resume Enhancer

> Full instructions: [Skills/resume-enhancer-v2/SKILL.md](Skills/resume-enhancer-v2/SKILL.md)
> Script: [Skills/resume-enhancer-v2/scripts/generate_resume.js](Skills/resume-enhancer-v2/scripts/generate_resume.js)

**Trigger:** `"Build my resume for [role title]. Here's the JD. Use my experience docs in the Experience folder."`

**What it does differently from a simple formatter:**
1. Decomposes the JD into required/preferred/leadership/domain skills
2. Indexes `career_timeline.json` to map JD skills to your experience — confirms every match with you *before* writing bullets; gaps are explicitly flagged
3. Writes bullets enforcing active voice (ban-list included), role-tier metric fit, and evidence anchor tracing
4. Runs `generate_resume.js` for consistent `.docx` formatting (`node scripts/generate_resume.js resume_data.json output.docx` — requires `npm install docx`)
5. Post-generation: independent subagent technical review (anchor traceability, date plausibility, claim credibility), then recruiter / hiring manager / interviewer persona reviews — all proposed edits require your approval

The `skill_evidence_map.json` artifact saved to the workspace shows exactly what drove each tailoring decision.

---

## Building the System

1. **Populate `career_timeline.json`** — fill in your roles, dates, skills, education, certifications. This is the index all downstream skills query.

2. **Run Skill 1 on 2–3 projects** — build your experience library before touching the Resume Enhancer. More library = better output.

3. **Add base resumes to `Resumes/`** — one per role level you're targeting.

4. **Run Skill 2 when applying** — provide the JD and point Claude at your Experience folder.

5. **Iterate** — both `SKILL.md` files are living documents. Edit them as you observe gaps.

---

## Possible Extensions

- **Cover Letter Skill** — reads JD + experience library, generates tailored cover letter
- **JD Analyzer Skill** — decomposes job descriptions into structured requirements both skills consume
- **Interview Prep Skill** — generates likely interview questions with answers drawn from your project history

Same pattern each time: focused skill + structured data = compounding value.
