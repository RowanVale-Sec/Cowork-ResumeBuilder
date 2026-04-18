#!/usr/bin/env node
/**
 * Resume Generator — produces a modern, professional .docx resume
 *
 * Usage: node generate_resume.js <input.json> <output.docx>
 *
 * The input JSON should have this structure:
 * {
 *   "name": "Full Name",
 *   "contact": {
 *     "email": "email@example.com",
 *     "phone": "+1 555 123 4567",
 *     "linkedin": "linkedin.com/in/username",
 *     "location": "City, State"
 *   },
 *   "summary": "Professional summary paragraph...",
 *   "sections": [
 *     {
 *       "type": "experience",
 *       "title": "Professional Experience",
 *       "entries": [
 *         {
 *           "company": "Company Name",
 *           "role": "Job Title",
 *           "dates": "Month Year – Present",
 *           "bullets": ["Achievement 1...", "Achievement 2..."]
 *         }
 *       ]
 *     },
 *     {
 *       "type": "skills",
 *       "title": "Technical Skills",
 *       "groups": [
 *         { "category": "Category Name", "items": "Skill 1, Skill 2, Skill 3" }
 *       ]
 *     },
 *     {
 *       "type": "education",
 *       "title": "Education",
 *       "entries": [
 *         {
 *           "institution": "University Name",
 *           "degree": "Degree Title",
 *           "dates": "Year – Year",
 *           "details": "Optional additional info"
 *         }
 *       ]
 *     },
 *     {
 *       "type": "certifications",
 *       "title": "Certifications",
 *       "items": ["Cert 1", "Cert 2"]
 *     },
 *     {
 *       "type": "list",
 *       "title": "Any Section Title",
 *       "items": ["Item 1", "Item 2"]
 *     }
 *   ]
 * }
 */

const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  TabStopType, TabStopPosition, LevelFormat, BorderStyle,
  HeadingLevel, WidthType, ShadingType
} = require('docx');

// ── Design tokens ──────────────────────────────────────────────
const ACCENT       = "1B3A5C";   // Deep navy blue — authoritative, executive
const ACCENT_LIGHT = "3D6B99";   // Lighter navy for subtle elements
const DIVIDER      = "C5D1DC";   // Soft blue-grey for divider lines
const BODY_COLOR   = "2D2D2D";   // Near-black for body text (softer than pure black)
const MUTED        = "5A5A5A";   // Muted grey for dates and secondary info
const NAME_SIZE    = 48;         // 24pt — commanding but fits on one line
const SECTION_SIZE = 22;         // 11pt — clear section headers
const BODY_SIZE    = 20;         // 10pt — professional body text, space-efficient
const SMALL_SIZE   = 18;         // 9pt — for contact info and dates
const FONT         = "Calibri";

// ── Styles ─────────────────────────────────────────────────────
const styles = {
  default: {
    document: {
      run: { font: FONT, size: BODY_SIZE, color: BODY_COLOR }
    }
  },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: SECTION_SIZE, bold: true, font: FONT, color: ACCENT, allCaps: true },
      paragraph: {
        spacing: { before: 200, after: 40 },
        border: {
          bottom: { style: BorderStyle.SINGLE, size: 4, color: DIVIDER, space: 4 }
        }
      }
    },
    {
      id: "Heading2", name: "Heading 2",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: BODY_SIZE, bold: true, font: FONT, color: BODY_COLOR },
      paragraph: { spacing: { before: 0, after: 0 } }
    }
  ]
};

// ── Numbering (bullets) ────────────────────────────────────────
const numbering = {
  config: [
    {
      reference: "resume-bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "\u2022",
        alignment: AlignmentType.LEFT,
        style: {
          paragraph: { indent: { left: 360, hanging: 180 } },
          run: { font: FONT, size: BODY_SIZE, color: ACCENT_LIGHT }
        }
      }]
    },
    {
      reference: "dash-bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "\u2013",
        alignment: AlignmentType.LEFT,
        style: {
          paragraph: { indent: { left: 360, hanging: 180 } },
          run: { font: FONT, size: SMALL_SIZE, color: MUTED }
        }
      }]
    }
  ]
};

// ── Helper: Name header ────────────────────────────────────────
function buildNameHeader(name) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [
      new TextRun({
        text: name.toUpperCase(),
        font: FONT,
        size: NAME_SIZE,
        bold: true,
        color: ACCENT,
        characterSpacing: 80 // Letter-spacing for executive feel, fits on one line
      })
    ]
  });
}

// ── Helper: Contact bar ────────────────────────────────────────
function buildContactBar(contact) {
  const parts = [];
  if (contact.phone) parts.push(contact.phone);
  if (contact.email) parts.push(contact.email);
  if (contact.linkedin) parts.push(contact.linkedin);
  if (contact.location) parts.push(contact.location);

  const children = [];
  parts.forEach((part, i) => {
    if (i > 0) {
      children.push(new TextRun({
        text: "  |  ",
        font: FONT, size: SMALL_SIZE, color: DIVIDER
      }));
    }
    children.push(new TextRun({
      text: part,
      font: FONT, size: SMALL_SIZE, color: MUTED
    }));
  });

  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 40 },
      children
    }),
    // Thin line under contact info
    new Paragraph({
      spacing: { after: 120 },
      border: {
        bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 6 }
      },
      children: [new TextRun({ text: "", size: 4 })]
    })
  ];
}

// ── Helper: Section header ─────────────────────────────────────
function buildSectionHeader(title) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text: title.toUpperCase() })]
  });
}

// ── Helper: Summary ────────────────────────────────────────────
function buildSummary(text) {
  return new Paragraph({
    spacing: { after: 60 },
    children: [
      new TextRun({
        text: text,
        font: FONT,
        size: BODY_SIZE,
        color: BODY_COLOR
      })
    ]
  });
}

// ── Helper: Experience entry ───────────────────────────────────
function buildExperienceEntry(entry) {
  const paras = [];

  // Role + Company line with right-aligned dates
  paras.push(new Paragraph({
    spacing: { before: 100, after: 10 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      new TextRun({
        text: entry.role,
        font: FONT, size: BODY_SIZE, bold: true, color: BODY_COLOR
      }),
      new TextRun({
        text: entry.company ? `  —  ${entry.company}` : "",
        font: FONT, size: BODY_SIZE, color: MUTED
      }),
      new TextRun({
        text: `\t${entry.dates || ""}`,
        font: FONT, size: SMALL_SIZE, color: MUTED, italics: true
      })
    ]
  }));

  // Bullet points
  if (entry.bullets && entry.bullets.length > 0) {
    entry.bullets.forEach(bullet => {
      paras.push(new Paragraph({
        numbering: { reference: "resume-bullets", level: 0 },
        spacing: { before: 15, after: 15 },
        children: [
          new TextRun({
            text: bullet,
            font: FONT, size: BODY_SIZE, color: BODY_COLOR
          })
        ]
      }));
    });
  }

  return paras;
}

// ── Helper: Skills section ─────────────────────────────────────
function buildSkillsSection(groups) {
  const paras = [];
  groups.forEach(group => {
    paras.push(new Paragraph({
      spacing: { before: 60, after: 30 },
      children: [
        new TextRun({
          text: `${group.category}: `,
          font: FONT, size: BODY_SIZE, bold: true, color: ACCENT
        }),
        new TextRun({
          text: group.items,
          font: FONT, size: BODY_SIZE, color: BODY_COLOR
        })
      ]
    }));
  });
  return paras;
}

// ── Helper: Education entry ────────────────────────────────────
function buildEducationEntry(entry) {
  const paras = [];
  paras.push(new Paragraph({
    spacing: { before: 80, after: 20 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      new TextRun({
        text: entry.degree,
        font: FONT, size: BODY_SIZE, bold: true, color: BODY_COLOR
      }),
      new TextRun({
        text: `  —  ${entry.institution}`,
        font: FONT, size: BODY_SIZE, color: MUTED
      }),
      new TextRun({
        text: entry.dates ? `\t${entry.dates}` : "",
        font: FONT, size: SMALL_SIZE, color: MUTED, italics: true
      })
    ]
  }));
  if (entry.details) {
    paras.push(new Paragraph({
      spacing: { after: 20 },
      indent: { left: 180 },
      children: [
        new TextRun({ text: entry.details, font: FONT, size: SMALL_SIZE, color: MUTED })
      ]
    }));
  }
  return paras;
}

// ── Helper: Certifications / simple list ───────────────────────
function buildSimpleList(items) {
  // Compact inline rendering: items separated by bullets on 1-2 lines
  return [new Paragraph({
    spacing: { before: 30, after: 30 },
    children: items.flatMap((item, i) => {
      const parts = [];
      if (i > 0) {
        parts.push(new TextRun({
          text: "   \u2022   ", font: FONT, size: SMALL_SIZE, color: ACCENT_LIGHT
        }));
      }
      parts.push(new TextRun({
        text: item, font: FONT, size: BODY_SIZE, color: BODY_COLOR
      }));
      return parts;
    })
  })];
}

// ── Main: Build document ───────────────────────────────────────
async function main() {
  const [,, inputPath, outputPath] = process.argv;

  if (!inputPath || !outputPath) {
    console.error("Usage: node generate_resume.js <input.json> <output.docx>");
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const children = [];

  // Name header
  children.push(buildNameHeader(data.name));

  // Contact bar
  if (data.contact) {
    children.push(...buildContactBar(data.contact));
  }

  // Summary
  if (data.summary) {
    children.push(buildSectionHeader("Professional Summary"));
    children.push(buildSummary(data.summary));
  }

  // Remaining sections
  for (const section of (data.sections || [])) {
    children.push(buildSectionHeader(section.title));

    switch (section.type) {
      case "experience":
        for (const entry of (section.entries || [])) {
          children.push(...buildExperienceEntry(entry));
        }
        break;

      case "skills":
        if (section.groups) {
          children.push(...buildSkillsSection(section.groups));
        }
        break;

      case "education":
        for (const entry of (section.entries || [])) {
          children.push(...buildEducationEntry(entry));
        }
        break;

      case "certifications":
      case "list":
        if (section.items) {
          children.push(...buildSimpleList(section.items));
        }
        break;

      default:
        // Fallback: treat as simple list or text
        if (section.items) {
          children.push(...buildSimpleList(section.items));
        }
        if (section.text) {
          children.push(buildSummary(section.text));
        }
        break;
    }
  }

  const doc = new Document({
    styles,
    numbering,
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 },  // US Letter
          margin: {
            top: 720,      // 0.5 inch
            bottom: 720,   // 0.5 inch
            left: 1080,    // 0.75 inch
            right: 1080    // 0.75 inch
          }
        }
      },
      children
    }]
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`Resume written to ${outputPath}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
