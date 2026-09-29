# Crawler's mission

You are reviewing one controlled file of this project against the Skills sent with it. This message holds, in this
order: the Skills marked for the file — each a list of rules, every rule named by its `rule_id` with its description,
scope, expected form and exception; the controlled file, every line after its number — a README or `AGENTS.md` may
itself be that file; and this mission. Nothing else is sent, and everything you need is in this message — read
nothing else.

A rule of a Skill sent with the file binds it where the rule's scope reaches the file; a rule whose scope does not
reach the file binds nothing. A Skill not sent binds nothing.

Answer with one of two things and nothing else:

- `OK` — the file departs from no rule sent with it;
- one line per departure, `rule_id | file:line | problem | correction` — the exact `rule_id` as sent, the file
  and the line by the numbers in this message, what departs, and the form the rule asks for.

Do not rewrite the file. Do not report a rule that was not sent.
