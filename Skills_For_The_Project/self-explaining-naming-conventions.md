# Skill: self-explaining naming conventions

Every name in this repository — a variable, a parameter, a function, a key —
must explain itself, so an agent never has to guess.

- **The name carries the information.** What a thing is, what it measures and
  in what unit are readable from the identifier alone, without opening another
  file — and without redundancy: a name repeats nothing its scope already
  states.
- **The measure is thoughts, not tokens.** A name is good when it minimises
  the number of thoughts an agent must think to use it correctly. Every
  obscure identifier forces a chain of decoding steps before the real work
  starts, and those steps are the cost — not the characters saved.
- **Self-explaining names are the interface.** Agents understand and extend
  this repository through its names; a name that needs a lookup turns every
  reader into an archaeologist.
- **One concept, one name.** A synonym forces the reader to decide whether two
  names are one thing or two — a thought the code should never demand.
- **The glossary confirms, it never decodes.** `glossary.md` registers what a
  name already says; if the register is needed to understand the name, the
  name is wrong.
- **Rename only what impedes reading.** A working, honest name stays; churn is
  its own cost.
