---
name: revise-paper
description: Revise research papers, especially Overleaf or multi-file LaTeX projects containing .tex, .bib, figures, build logs, and a compiled PDF. Use for professor-led manuscript revision, reverse outlining, LaTeX proofreading, cross-file consistency, figure/table/equation review, BibTeX cleanup, anonymization, or final submission readiness. Preserve student authorship and research claims; never invent evidence, citations, results, or author contributions.
license: CC BY-NC-SA 4.0
---

# Revise Paper

Revise the LaTeX sources as the editable authority and use the compiled PDF as the visual authority. Inspect the entire project, make traceable changes, and deliver a revision report summarizing automatic changes, suggested changes, and comments. These three types of output will be specified for each revision instruction, e.g., *automatic change*, *suggested change*, *comment*.

- Automatic changes: Automatically revise the TeX files without asking for permission. This typically applies to typos, grammar, and format issues.
- Suggested changes: Suggest changes for specific parts of the paper in the report, but do not automatically revise the TeX files. The user should review them before incorporating such changes.
- Comments: Make comments on specific parts of the paper in the report. Do not automatically revise the TeX files.

## Revision setup: understand files

1. Identify the project root, main TeX file, TeX files for each section, bibliography files, figures, build configuration, and compiled PDF.
2. If the input is an Overleaf ZIP, preserve the archive and extract it to a new, clearly named working directory. Reject unsafe archive paths that escape that directory.
3. If the entire paper's content is in a single main TeX file, split it into multiple TeX files by section, e.g., 0_abstract.tex, 1_introduction.tex, 2_related_work.tex, and then use \input{} for each section in the main TeX file. *automatic change*
4. Inspect version-control status before editing. Preserve all existing user changes and never discard or overwrite unrelated work.
5. Work on the supplied project or a clearly named copy. Do not edit the compiled PDF as a substitute for editing the sources.
6. Do not change submission ID, author names, order, affiliations, acknowledgments, participant counts, measurements, statistical results, or substantive claims without explicit support and instructor approval.

## Revision setup: compile baseline PDF

1. Determine the intended engine and build command from project files, Overleaf settings, comments, or the existing build workflow. Do not assume `pdflatex` when XeLaTeX or LuaLaTeX is required.
2. Compile without changing sources. Prefer the project's existing command; otherwise use `latexmk` with the detected engine.
3. Keep built artifacts outside source directories when practical.
4. Save the baseline log and PDF. If local compilation is unavailable, use the supplied compiled PDF and state that limitation.
5. Render every baseline PDF page to images and inspect at readable size. Text extraction alone cannot validate figure legibility, page flow, widows/orphans, clipping, or anonymization.

## Revise outline

1. Title: Check if it is appropriate, clear, unambiguous, and correctly capitalized following the APA style guide. Check the correctness of articles, singular/plural forms, and prepositions. *comment*
2. Abstract: Check if it is clear, if there is a coherent logic between sentences, and if it highlights the paper's contributions. *comment*
3. Each section and subsection: Check if the sections and subsections are reasonable and well structured. The section and subsection titles should be correctly capitalized following the APA style guide. *comment*
4. For each paragraph, check if its first sentence can serve as the topic sentence with a clear controlling idea when the genre permits. Check if the first sentences of each paragraph can form a coherent logic flow. *comment*

## Revise introduction

1. Summarize the structure of the introduction. Check if a quick introduction read reveals the problem, novelty, approach, validation, and takeaways. *comment*
2. Check if the first one to two paragraphs clearly introduce the background and motivation of this research. They should clearly define the research problem and explain why it is important and difficult, i.e., the research gap. *comment*
3. The last paragraph typically contains three bullet points describing the contributions. Check if the contributions are described clearly and meaningfully without potential overclaims. *comment*

## Revise related work

- Related work should cover a few subsections reviewing distinct yet connected research fields. Check if each subsection progresses from field overview, through representative work, to the specific research gap relative to the current paper. *comment*

## Revise writing

Prefer targeted changes over wholesale paragraph replacement.

*automatic changes*:
- Define an abbreviation in full at first use and use one form consistently thereafter.
- Use past tense for completed experimental procedures and observations; use present tense for established facts, interpretations, and conclusions.
- Use `i.e.,` and `e.g.,` with correct punctuation and without automatic italics.
- Avoid using `&` or `/` in the main text for formal writing. Use `and` or `or` instead.
- Replace quotation marks “” "" ＂＂ with correct LaTeX quotation marks ``''. Punctuations like commas and periods should go inside the quotation marks.
- Follow established hyphen/en-dash/em-dash conventions consistently. In LaTeX, do not use `–` `—` directly; use `-` for hyphen, `--` for en-dash, and `---` for em-dash. There should be no space between the dashes. Use en-dashes for ranges. Avoid stylistic overuse of em-dashes and parenthetical asides.
- Ensure whitespace is correctly added between sentences and before a left parenthesis.

*suggested changes*:
- Check whether singular and plural terms are properly used. Plural forms are typically used for `objectives`, `limitations`, `preliminaries`, etc.
- Use consistent terms for concepts, modules, datasets, and baselines.
- Avoid long noun stacks.
- Prefer active constructions when they improve clarity, but do not mechanically eliminate all passive voice.
- Avoid broad praise such as "innovative" or "amazing" unless with sufficient evidence.
- Check whether prepositions are properly used. Prepositions should express meaningful relationships.

## Revise figures and tables

Inspect the rendered PDF rather than judging source dimensions alone.

*automatic changes*:
- In the main text, refer to figures and tables as their captions appear. For example, use `Fig.~\ref{...}` in LaTeX if the caption appears `Fig.` Use `Figure~\ref{...}` for `Figure`. Use `Table~\ref{...}` for `Table`.
- Caption should appear at the bottom of a figure and at the top of a table.
- Check caption capitalization and terminal punctuation consistently. Caption capitalization should be in sentence case, not title case.

*suggested changes*:
- Each figure or table should have a unique label in LaTeX and be referenced in the main text.
- Check if there are broken figure and table references like `??`.
- Make captions self-contained and lead with a noun phrase as the caption title, not a complete sentence. Complete sentences can follow the caption title.

*comments*:
- Keep the teaser figure easy to scan: show what the paper does without loading them with unnecessary technical detail.
- Check if all figures are in vector format, wherever possible. Diagrams made in PowerPoint should be exported as PDF. The raster images should have a sufficient resolution.
- Text in figures and tables should use a similar font size and type to the main text. Use Linux Libertine for SIGGRAPH submissions.
- Make figure reading order obvious, usually left-to-right and top-to-bottom.
- Colors used in figures should consider aesthetics and accessibility. Use a restrained palette; split overcrowded graphics rather than adding many colors.

## Revise equations

*automatic changes*:
- Make every displayed equation part of a grammatical sentence and punctuate it accordingly.
- Use `\cdot` for multiplication and `\times` for dimensions; do not use `*` as formal multiplication.
- Set descriptive subscripts and textual material in roman text, normally with `\mathrm{}` or `\text{}` as appropriate. Keep mathematical variables italic.

*comments*:
- Define each symbol at first appearance and assign it only one meaning.
- Check formula references, numbering, alignment, overflow, and notation consistency in the compiled PDF.

## Revise references

### Source authority

*comments*:
- Prefer BibTeX supplied by the official publisher or digital library, such as ACM Digital Library, IEEE Xplore, CVF Open Access, or Eurographics Digital Library.
- Do not treat Google Scholar exports as authoritative; they may be incomplete or incorrectly formatted.
- Prefer the final published version over an arXiv or preprint record when the published version exists.
- Verify metadata before changing it. Do not infer a DOI, page range, venue, author order, or publication year.

### Entry integrity

*automatic changes*:
- Use a unique, stable citation key, e.g., "Wang2021Tracing." If the citation key is changed in BibTeX, ensure all references in the TeX files are also changed accordingly.
- Paper titles and venue names should be correctly capitalized in title case. Preserve capitalization for proper nouns, acronyms, software, place names, "3D," and other case-sensitive terms reliably with braces.
- Escape TeX-sensitive characters such as `&` and `%`.
- Use `--` for numeric page ranges in BibTeX.
- Use a suitable `@misc` or venue-prescribed entry for websites and include author or organization, title, URL, year when known, and access date when required.

### Consistency

*automatic changes*:
- Use one form for each journal and conference name across the bibliography. Do not mix abbreviations and full names unless the bibliography style intentionally controls them.
- Confirm every citation in TeX is in the form of `~\cite{}`, every citation resolves, and every rendered reference is cited.
- Confirm no citation or reference renders as `?`, `??`, or an undefined marker.
- Confirm every `~\cite{}` does not function like a noun component in a sentence. If a noun component is needed, use `\citet{}` or name the authors or work explicitly.

### Verification

*comments*:
1. Audit all bibliography files, including files not selected by the main document. Absolutely no fabricated citations.
2. Compile through the full bibliography cycle.
3. Inspect build warnings for undefined citations and multiply defined labels.
4. Inspect the rendered reference section for capitalization, missing fields, wrapping, and consistency.
5. Report metadata that could not be verified rather than silently "correcting" it.

## Revise layout

*suggested changes*:
- Remove widows, orphans, lone words, awkward wrapping, clipped content, and excessive whitespace without compromising content.
- Figures and tables should be close to their references in the main text in the rendered PDF, ideally on the same page.

## Final check

*comments*:
- Keep the main paper self-contained when appendices or supplementary materials are present.
- Ensure the paper and supplementary materials are anonymized. Identify any information that may reveal author identities, including custom macros in LaTeX and external URLs in the paper.
- Ensure there is a discussion of limitations in the paper.
- Use the present perfect tense in the first sentence of the conclusion, e.g., "We have presented ..."
- Proofread the full paper again to fix issues and improve clarity.
- Fix every Overleaf/compiler error and eliminate undefined references, missing citations, and visible placeholders.

## Output

Keep the revised LaTeX project usable in Overleaf. Return a concise report summarizing automatic changes, suggested changes, and comments. They should be clearly numbered and accurately located in the source files. The suggested changes and comments can be automatically incorporated if the user wishes.
