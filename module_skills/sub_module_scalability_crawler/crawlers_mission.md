# Crawler's mission

You are reviewing one file of this repository against its written rules. The rules follow this
mission, each under its path — the canon, then the orientation and the skills of the file's own
module; the file follows them, under its own path, every line after its number. Everything you
need is in this message — read nothing else. A placement argued in a document this message does
not carry is no departure: report it as unexplained.

Report, in this order, with `none` under an empty section:

1. **Departures.** One line per rule the file departs from: `<rule path> § <section>`; the rule's
   deciding clause, quoted verbatim; every line of the file it touches, by the numbers in this
   message; the current form, quoted verbatim from those lines; the form the rule derives.
2. **Unexplained.** One line per item a reader cannot decode from the file and the rules alone:
   its line numbers, and the missing sentence, written out — a docstring, a comment or a
   `§ Design rationale` row — that would explain it. A pattern no rule governs belongs here when it
   is seen exactly twice, or when it misses one of the conditions of section 3.
3. **Proposed conventions.** A pattern seen three times or more that no rule governs, one block per
   pattern: the pattern and every occurrence by line number, then the seven conditions of
   `module_skills/skill_self_explaining_naming.md` § Minting a new convention, one field each —
   closed list, derivable, normative source, able to fail (the form it forbids), scope, boundary,
   migration cost.
4. One closing line: `conformant`, or `departures: <n>` with n the number of lines of section 1.

Mark a section with its bold label, never a Markdown heading: the entry already sits under the
report's own heading. Quote a rule's deciding clause, never paraphrase it. Propose, never decide. Do not rewrite the file.
