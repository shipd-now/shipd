## 1. Skill flow hardening

- [x] 1.1 [req: investigation-findings-digest] In
      `plugins/s/skills/plan/SKILL.md`, insert a new Flow step between
      "Investigate" and "Depth gate": **Report findings** — print a short
      user-visible findings digest (affected files/capabilities, relevant
      existing behavior and patterns, anything surprising) as plain response
      text, before the gate verdict and before any AskUserQuestion; internal
      reasoning does not count. Renumber the subsequent steps and fix any
      step-number cross-references in the file.
- [x] 1.2 [req: context-brief] In `plugins/s/skills/plan/SKILL.md` (fast-path
      question contract) and
      `plugins/s/skills/plan/references/dialogue.md` (context-brief
      section), state that the brief is a precondition of the
      AskUserQuestion call: it must be user-visible response text (never only
      internal reasoning), and a decision-resolving call whose turn did not
      first present the visible brief is a protocol violation — do not issue
      the call until the brief is printed.
- [x] 1.3 [req: visualization-on-demand] In
      `plugins/s/skills/plan/references/visualization.md`, add the explicit
      user-request override to the prohibition paragraph: a request that asks
      for a diagram satisfies the carries-a-decision bar by itself, and the
      requested solution diagram appears no later than the first context
      brief (or in the findings digest when no question round occurs). In
      `plugins/s/skills/plan/SKILL.md`, name the override where the
      visualization reference is pointed at.

## 2. Missing-layout guard

- [x] 2.1 [req: missing-layout-guard] In
      `plugins/s/skills/plan/SKILL.md`, replace the bare layout
      requirement sentence with the guard: when the repo lacks the `am/`
      layout, stop before any questioning, report it, and ask one
      AskUserQuestion — scaffold `am/verified/`, `am/planned/`,
      `am/completed/` and continue (recommended) or stop; never proceed as
      though the layout existed.

## 3. Version

- [x] 3.1 [req: *] Bump `plugins/s/.claude-plugin/plugin.json` version from
      0.2.9 to 0.2.10 (plugin content changed: plan skill and two
      references edited).
