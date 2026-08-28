# Skill: sorting files naming standard

A directory listing is read by eye before any parser reads it, and every
machine sorts it lexicographically — so a name is designed for the order it
will land in, on any server, under any locale.

- **The kind comes first, so one kind is one block.** `module_*` beside
  `module_*`, `store_*` beside `store_*`, `skill_*` beside `skill_*`: the eye
  takes a contiguous block for free, while a kind scattered through the
  alphabet charges a scan and a memory for every lookup.
- **Digits sort before letters — build granularity order on that.** In ASCII
  the digits (0x30–0x39) precede every letter, so a slot filled with a number
  beats a letter placeholder at the same position. The timeframe slot standard
  `ss-mm-hh-dd-MM` (the act, § timeframe slots) uses exactly this: 1-minute
  data is `ss-01-hh-dd-MM`, 1-hour is `ss-mm-01-dd-MM`, and every listing
  orders them finest to coarsest without any tool knowing what a timeframe is.
- **Zero-pad every number.** `01 < 04 < 15` sorts numerically as text;
  unpadded `1, 4, 15` sorts as `1, 15, 4`. Two digits per slot until a real
  name needs three.
- **Fixed width aligns columns.** Slots of constant width make sibling names
  line up character for character, so a difference is visible at the exact
  position where it lives — the listing becomes a table without a table.
- **Design for every collation at once.** `LC_COLLATE=C` compares bytes;
  UTF-8 locales fold case and punctuation; macOS and Windows filesystems
  compare case-insensitively. A standard survives them all when its order
  never depends on case or punctuation alone — digits-before-letters holds
  everywhere, which is why the slot scheme was verified identical under both
  `C` and `en_US.UTF-8` before it was enacted.
- **The enacted names live in the act.** This skill explains the mechanics;
  `act_naming_conventions.md` records which exact names the project decided,
  with the rejected forms. A new sortable pattern is minted like any other
  convention: closed vocabulary, derivable, grep-checkable, able to fail —
  and enters the act in the commit that enacts it.
