# Visualization on demand — diagrams that carry a decision

Loaded on demand **at most once per session** — from the depth-path dialogue
(`dialogue.md`) the first time a visual would actually carry a decision being
put to the user, or from either path when the user's request explicitly asks
for a diagram (see the override below).
A visual earns its place only when it makes a choice clearer than prose would;
everything here is in service of a decision on the grill-loop agenda.

**Prohibition on decorative visuals — in question rounds.** In a question
round, never emit a diagram or table that does not carry a decision. If a
choice is clear from one sentence of prose, ask it in one sentence of prose and
do not load or use this reference. Ornamental architecture diagrams,
restating-the-obvious flowcharts, and "here's the system" pictures with no
pending decision are all out of scope for question rounds.

**The findings digest is lean-toward, not prohibition.** The digest is the one
place the bar relaxes: a proposed shape or flow in the findings satisfies the
carries-a-decision bar **by itself**, because the digest's shape is what the
user judges to catch a wrong direction before emission — their one chance to
redirect now that the flow proceeds without asking. So when the findings carry
a shape a compact diagram conveys faster than prose, the digest includes one —
no separate pending decision required. See the "digest shape sketch" idiom
below. A shapeless single-file tweak still needs no diagram.

**The one exception — an explicit user request.** When the user's request
explicitly asks for a diagram or visual ("draw me a diagram of the solution"),
that request satisfies the carries-a-decision bar by itself. Honor it: present
the requested solution diagram no later than the first context brief — or in
the investigation findings digest when no question round occurs. The
prohibition above applies only to visuals nobody asked for; it never overrides
an explicit request.

## When a visual pays

Use a visual when the decision turns on a *shape* the user must see to judge:

- **Current-vs-proposed** — the choice restructures something that already
  exists; the user needs to see before and after side by side.
- **Flow / sequence** — the decision is about ordering, control flow, or where a
  step lands in a pipeline.
- **Options comparison** — two or more candidates trade off along the same axes,
  and the trade is easier read as a table than as prose.

## ASCII idioms

Keep diagrams small, monospace-friendly, and inline. They are decision aids, not
documentation.

**Current-vs-proposed map** — put the two states next to (or above) each other
with the delta called out:

```
current:   request → [batch questions once] → readiness → emit
proposed:  request → [depth gate] → grill loop (grouped rounds) → summary → emit
                         └─ fast path unchanged when 0–1 signals
```

**Flow sketch** — a linear or branching pipeline where the decision is about
order or placement:

```
investigate ─▶ gate ──0–1 signals──▶ fast path
                 └────≥2 signals────▶ depth path ─▶ grill loop ─▶ summary
```

**Options table** — candidates as rows, decision axes as columns, with a
recommended row marked:

```
option              | task-list impact | blast radius | recommend
--------------------|------------------|--------------|----------
A: extend SKILL.md  | small            | one file     | ✓
B: new explore skill| large            | new skill    |
```

**Digest shape sketch** — the compact proposed-shape diagram the findings
digest leans toward: a small map of the components or flow the change
introduces, so the user judges the shape at a glance before the flow proceeds
to emission. Not a decision between candidates — just the one shape the
findings propose:

```
proposed:  investigate ─▶ findings digest ─▶ depth gate
                              └─ headed dot-point groups (+ this sketch)
```

## Per-option visuals — inline in the typed round, `preview` only for prose-free dialogs

Rounds are **typed plain-text** — the depth-path grill rounds and the fast
path's batched round alike — so per-option visuals ride **inline in the brief's
message**: give each option its own small diagram or table next to its numbered
entry, so the user compares the candidates visually before typing a reply. Keep
each option's visual to the one shape that distinguishes it — the same "carries
a decision" bar applies per option.

The AskUserQuestion **`preview`** field is reserved for the one case a dialog is
still permitted — a single self-contained question in a prose-free turn (no
brief or other substantive prose). There, attach the per-option visual using the
question's `preview` field instead, giving each option its own small diagram or
table under the same per-option bar.
