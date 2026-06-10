---
name: glavlab-protocol-review
description: Use when reviewing one or more construction protocol PDFs, especially GLAVLABGROUP test protocols, to find only confirmed formatting, logic, calculation, date, header, footer, table, and required-field errors with precise localization and a concise fix-ready report.
---

# GLAVLAB Protocol Review

## When To Use

Use this skill when the user asks to check one or more PDF protocols for errors, omissions, formatting defects, or rule violations.

This skill is especially for GLAVLABGROUP construction protocols and should be treated as the primary review workflow when attached.

## Core Goal

Find only confirmed issues. Prioritize accuracy over coverage and avoid speculative findings.

Return a concise report that is easy to fix from, with exact localization for each issue.

## Review Order

Use sources in this order:

1. The current user request and any explicit checklist or correction the user supplied.
2. The PDF itself.
3. Attached agent files and templates that clarify expected structure or wording.
4. Saved Memory rules and confirmed exceptions that the user previously approved.

If a user-provided checklist conflicts with a weaker implied convention, follow the checklist.

## Main Workflow

1. Determine how many distinct protocols are inside each uploaded PDF.
2. Split your reasoning by protocol. Never mix findings across different protocols.
3. Identify the protocol type. At minimum distinguish: УК, КП, КУ, ВС.
4. Run general checks across structure, dates, numbering, headers, footers, tables, required fields, performers, formulas, and obvious layout defects.
5. Run type-specific checks for the detected protocol type.
6. Collect findings by page and sort them by severity.
7. If a fragment is unreadable or visually ambiguous, mark the limitation and do not invent a finding.

## Mandatory Checks

Always check, when applicable:

- protocol number in the header
- protocol number in the footer
- consistency between header and footer
- broken, duplicated, or malformed numbering
- dates and their logical consistency
- validity periods of checks and calibrations relative to the test date
- calibration formula correctness
- sequence of line numbers inside one protocol
- table borders, broken corners, missing top or right lines, and visual table defects
- required fields being filled
- performer names and roles
- obvious typos, broken symbols, clipping, and layout defects

Do not limit the review to text-only mistakes. Clear visual defects are also valid findings.

## Type-Specific Rules

### УК

Check structure age, repeated structures, structure names, duplicate structures, axis labels, percentages from design class, calibration details, row numbering, merged cells, and table formatting.

### КП

Check design class, required strength, reduced strength, average strength, percentage from required strength, production date, test date, age, sample dimensions, and the correctness of concrete or mortar grade labels.

Calculate percentage only as:
`average strength / required strength * 100`

Never calculate that percentage from destructive load.

### КУ

Check compaction coefficient, required coefficient, conclusion consistency with table values, right side of the table, last columns, right border, and closed table geometry.

### ВС

Check required fields, illumination level, equipment, control type, welding method, GOST, performers, and conclusion.

Treat the field "Уровень освещенности" as filled if a nearby value with the unit `лк` is clearly present.

## Confirmed Exceptions

Apply these standing exceptions unless the user overrides them:

- For `№.КП` protocols, absence of a footer is not an error.
- For `№.КП` protocols, do not treat page numbering issues as findings.
- Service page numbering in the footer is not automatically an error.
- If one PDF contains multiple protocols and the footer shows the page count for the whole export package, do not turn that alone into a separate error.
- Phrases like `менее 28 суток` and `более 28 суток` are not errors by themselves.
- If structure age is exactly `28` days and the conclusion says `более 28 суток`, do not flag it.
- If concreting date is shown as a range, compute age from the latest date in that range.
- Never treat a line like `Используемая градуировочная зависимость: R=...` as the calibration date.
- If an equation like `R=...*H...` has no `+` or `-` sign after `H`, that is a real error.
- Different `b` coefficients in otherwise similar calibration equations are not automatically errors; at most flag them as attention points.
- `//` in axis labels is not automatically an error.
- Do not treat a field as empty if its value is clearly moved to the adjacent line.
- For ВС protocols, absence of `Материал по проекту` is not an error.
- For ВС protocol headers, do not flag missing GOST mention as a separate error.
- PDF assembly artifacts where a line from a neighboring page intrudes visually are not protocol defects.

## Localization Rules

For every finding, provide the most precise location available:

- page
- protocol
- block, row, cell, column, field, formula, header, or footer

If the issue is in a row number, point to the specific `№ п/п` cell.
If the issue is in table geometry, describe the broken border or open corner exactly.
If the issue is in a header or footer, say which one.

Avoid vague locations like "somewhere on the page".

## Output Format

Structure the result like this:

1. short file summary
2. list of protocols if there is more than one
3. severity summary: critical, important, minor
4. findings grouped by page or protocol section

Format each finding as:

- severity
- location
- problem
- how to fix
- basis for check

Keep each finding short and separate.

If no issues are found, explicitly say that no confirmed issues were found and briefly list what was checked.

## Safety

- Do not invent defects.
- Accuracy matters more than completeness.
- Never merge evidence from different protocols.
- Do not claim regulatory, technical, or legal non-compliance without enough support.
- When evidence is ambiguous, prefer a note about uncertainty over a false-positive finding.
