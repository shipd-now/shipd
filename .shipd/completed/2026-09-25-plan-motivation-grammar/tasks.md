## 1. The harness long-form reference

- [x] 1.1 [req: plan-document-sections] In
      `plugins/s/harness/references/plan.md`, replace the one-line
      `### Motivation` rule (currently "Why this is being done, in the
      repository's terms.", around line 66) with a short block stating: at
      most two sentences naming who is blocked and what they cannot do;
      repository state may be cited as evidence for that claim but is never
      the claim itself — that a file is a placeholder or holds particular
      content is not on its own a reason; and a motivation that cannot be
      grounded goes to the user rather than being invented. Keep the
      surrounding `## Idea` / `### Details` / `### Non-goals` structure and
      heading levels exactly as they are.

## 2. The plan skill's authoring surfaces

- [x] 2.1 [req: plan-document-sections] In
      `plugins/s/skills/plan/references/emission.md`, rewrite element 2 of the
      `## Idea` list (the `**### Motivation**` bullet, around lines 121-125) so
      it keeps the "at most two sentences" limit and the never-a-guess rule,
      and adds the content bar: the sentence must name the affected party and
      what they cannot do, with repository state admissible as evidence for
      that claim and never as the claim itself. Leave elements 1, 3 and 4
      (summary, `### Details`, `### Non-goals`) unchanged.
- [x] 2.2 [req: plan-document-sections] In the same file, leave the
      `dark-mode-toggle` worked example's `### Motivation` text unchanged — it
      already models the required shape ("users on OLED displays report eye
      strain at night… and there is no way to switch") — and add one sentence
      immediately after the example's code fence pointing at that motivation as
      the shape the rule asks for.
- [x] 2.3 [req: plan-document-sections] In
      `plugins/s/skills/plan/references/readiness.md`, extend checklist item 1
      (around lines 13-21) so it tests two things: that the motivation is
      grounded rather than guessed (the existing rule, kept verbatim in
      substance, including the direction to put an un-inferrable motivation to
      the user), and that it names who is blocked and from what. State
      explicitly that a motivation which only reports a file's current state
      does not discharge the item.

## 3. The format-authority README

- [x] 3.1 [req: plan-document-sections] In `.shipd/README.md`, update the
      `**## Idea**` bullet's parenthetical describing `### Motivation` (around
      lines 118-121) to match the amended capability text: at most two
      sentences on why the change is being made, naming who is blocked and
      what they cannot do, grounded in the planning context and never a guess,
      with repository state admissible as evidence but not as the claim.

## 4. Plugin version

- [x] 4.1 [req: *] Bump `"version"` in `plugins/s/.claude-plugin/plugin.json`
      from `0.6.231` to `0.6.232`. AGENTS.md requires this in the same PR for
      any change touching `plugins/s/`: the cache snapshot is keyed by version,
      so without the bump `claude plugin update s@shipd` is a no-op and sessions
      keep loading the old guidance this change exists to replace.

## 5. Verify

- [x] 4.1 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/build/tests` and `python3 -m unittest discover -s
      evals/tests` and confirm both exit 0 with no failures — the baselines are
      3119 and 65 tests respectively, both `OK`.
- [x] 4.2 [req: *] Confirm the four edited surfaces agree with each other and
      with the amended capability: grep `### Motivation` across
      `plugins/s/harness/references/plan.md`,
      `plugins/s/skills/plan/references/emission.md`,
      `plugins/s/skills/plan/references/readiness.md` and `.shipd/README.md`,
      and check each states both halves — names-who-is-blocked and
      never-a-guess — and that none of them still asks for the motivation "in
      the repository's terms".
