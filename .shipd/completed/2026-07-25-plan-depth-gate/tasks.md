## 1. Depth gate in SKILL.md

- [x] 1.1 [req: depth-gate] In `plugins/s/skills/plan/SKILL.md`, insert a
      "Depth gate" step between investigation and asking in the `## Flow`
      section: list the five signals verbatim from the plan's Implementation
      section, the 0–1 → fast / ≥2 → depth threshold, the verbal overrides
      ("grill me" → depth, "just plan it" → fast, overrides always win), and
      the requirement to announce the selected mode in one sentence. Point the
      depth branch at `references/dialogue.md`.
- [x] 1.2 [req: batched-user-questions] In the same `SKILL.md`, retitle and
      reword "The question contract (AskUserQuestion)" so every rule is
      explicitly scoped to the fast path, and add one line stating that on the
      depth path the dialogue reference's one-decision-per-question protocol
      governs instead. Remove no fast-path rule.

## 2. Depth-path references

- [x] 2.1 [req: grill-loop, shared-understanding-summary] Create
      `plugins/s/skills/plan/references/dialogue.md` with the grill-loop
      protocol: build an agenda of open task-shaping decisions from readiness
      item 4; resolve one decision per single-question AskUserQuestion with
      the recommended option listed first; apply the fact/decision test
      (discoverable → read, never ask); fold each answer back into the agenda;
      end when no open decision would change the task list; past roughly six
      agenda items, suggest `/s:epic` instead of continuing. Close with the
      shared-understanding summary contract: problem, chosen approach,
      decisions with one-line rationale, known risks, confirmed via a final
      AskUserQuestion whose recommended option is "emit".
- [x] 2.2 [req: visualization-on-demand] Create
      `plugins/s/skills/plan/references/visualization.md`: when a visual
      carries a decision (current-vs-proposed maps, flow sketches, options
      tables), ASCII idioms for each, use of the AskUserQuestion `preview`
      field for per-option diagrams, and the prohibition on decorative
      visuals. In `dialogue.md`, add the load rule: read this file at most
      once per session, the first time a visual would pay.

## 3. Version bump and review

- [x] 3.1 [req: *] Bump `version` in
      `plugins/s/.claude-plugin/plugin.json` from `0.2.3` to `0.2.4`.
- [x] 3.2 [req: *] Re-read the edited `SKILL.md` together with
      `references/readiness.md`, `references/emission.md`,
      `references/dialogue.md`, and `references/visualization.md` and confirm
      no rule contradicts another across fast and depth paths (batching scoped
      to fast path only; readiness gate unchanged as the terminator for both
      paths; emission still silent). Fix any contradiction found.
