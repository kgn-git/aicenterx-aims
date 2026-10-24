---
schema_version: 1
description: Tone and manner for user-facing copy — voice, messages and form; locale, formats and glossary are blanks this project fills in.
globs: ["**/*.{tsx,jsx,vue,svelte,astro,html}", "**/{locales,locale,i18n,messages,copy}/**"]
load: disk
---

<!-- Generated from 3C ux pack — see claudecodecoach.invalid. -->

Tone and manner for user-facing copy.

This pack ships with blanks. Replace every double-braced token below with this project's value;
`3c doctor` warns until none is left.

| Blank | What to put there |
| --- | --- |
| LOCALE | The language and region the copy is written in, e.g. a BCP 47 tag. |
| SPELLING | The spelling convention, e.g. which dictionary decides. |
| DATE_FORMAT | How a date is written in running text and in tables. |
| NUMBER_FORMAT | Decimal and thousands separators, and how units and currency are written. |
| GLOSSARY | The one word this product uses for each idea, and the words it does not use. |

Voice:

- Copy MUST be calm, plain and factual.
- Copy MUST address the user as "you", never as "we" or "I".
- Copy MUST use the user's words for the business, never ids, error names or technical terms.

Messages:

- A message MUST say what happened, then what the user can do next.
- A refusal MUST explain the rule that applies, never blame the user.
- An irreversible action MUST ask a question naming the thing and the consequence, and its confirming button MUST repeat the verb.
- An empty state MUST name the consequence and the next step.
- Advice, a hint or warning that blocks nothing, MUST say that it blocks nothing.

Form:

- Headings, labels and buttons MUST use sentence case.
- A button MUST be a verb plus an object.
- A sentence SHOULD carry one idea.

This project's choices:

- Language and region: en-GB.
- Spelling: British, -ise endings (organisation, authorise, behaviour, centre), Collins English Dictionary. The product name "AI Center X" keeps its own spelling.
- Dates: `18 October 2026` in running text; ISO `2026-10-18` in tables and data.
- Numbers: point for decimals, comma for thousands (`12,500.5`); a space between number and unit (`45 s`, `20 ms`), none before `%`.
- One word per idea: "initiative" (not use case, project or AI system); "AI Canvas" for the seven-block canvas; "film" for a simulation film (not video or animation).
