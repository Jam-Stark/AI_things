# Revise Paper

A Codex skill for systematically revising research papers stored as Overleaf or multi-file LaTeX projects.

`revise-paper` examines the manuscript as both source code and a rendered document. It can compile the project, revise safe language and formatting issues, inspect the paper's argument and organization, audit figures and references, and produce a source-located report for changes that require scholarly judgment.

## What it reviews

- Paper structure, reverse outline, and narrative flow
- Title, abstract, introduction, related work, and conclusion
- Grammar, terminology, abbreviations, tense, and LaTeX typography
- Figures, tables, captions, cross-references, and reading order
- Equations, notation, punctuation, and symbol definitions
- BibTeX metadata, citation usage, and undefined references
- Page layout, visual defects, anonymization, and submission readiness
- Build warnings and errors across a multi-file LaTeX project

The skill treats the LaTeX sources as the editable authority and the compiled PDF as the visual authority.

## Review model

The workflow separates findings by how much scholarly judgment they require:

| Class | Behavior | Typical examples |
| --- | --- | --- |
| Automatic changes | Edits the LaTeX source directly | Typos, clear grammar errors, whitespace, unambiguous formatting |
| Suggested changes | Reports a proposed revision for human review | Structural rewrites, terminology choices, unclear technical prose |
| Comments | Reports questions or concerns without rewriting | Unsupported claims, missing motivation, weak validation, ambiguous contributions |

## Requirements

- Codex with support for local agent skills
- An Overleaf project folder or exported ZIP archive
- A working LaTeX toolchain, preferably including `latexmk`
- The compiled PDF when available
- A PDF renderer for page-by-page visual inspection

## Installation

Install it in your personal skills directory:

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/CISLab-HKUST/revise-paper.git ~/.agents/skills/revise-paper
```

## Usage

Invoke the skill explicitly in Codex:

```text
Use $revise-paper to revise this Overleaf project.
```

## Recommended project input

The skill is designed to work with complete paper projects rather than isolated paragraphs:

```text
paper/
├── main.tex
├── sections/
│   ├── 1_introduction.tex
│   ├── 2_related_work.tex
│   └── other sections
├── references.bib
├── figures/
├── main.pdf
└── build files or logs
```

It can also accept an Overleaf ZIP export. The main entry point, bibliography files, figure assets, custom style files, and venue template should remain together.

## Contributing

Issues and pull requests are welcome. Changes to `SKILL.md` should remain concise, executable, and conservative about research content.

## License
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
