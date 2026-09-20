## 1. Rework the attestation contract

- [x] 1.1 [req: readiness-attestation, premise-evidence-in-attestation]
      Rewrite the "Attestation" section of
      `plugins/s/skills/plan/references/readiness.md`: the printed form is
      four `**<item name>** — <plain statement>` entries in checklist order
      plus a closing `Full evidence: <absolute plan.md path>` line (change
      name resolved first, per `emission.md`'s naming rule); the full
      evidence moves to the emitted `plan.md`'s `## Readiness attestation`
      section — one level-3 subsection per item, plain statement above an
      `Evidence:` dot-point list, citation standards unchanged,
      runnable-premise invocations and observations under item 3, phrasing
      avoiding the context gate's placeholder markers.
- [x] 1.2 [req: readiness-attestation] In
      `plugins/s/skills/plan/references/emission.md`, document the
      `## Readiness attestation` plan.md section after the QA-ledger grammar
      (subsection names, statement-above-evidence order, marker caution) and
      note in "Pick the change name" that the name is already resolved by the
      time the attestation prints.
- [x] 1.3 [req: readiness-attestation] Update step 5 of
      `plugins/s/skills/plan/SKILL.md`: print the plain attestation
      (statements plus path line) instead of "a markdown table with one cited
      row", with the full evidence authored into the staged `plan.md`'s
      `## Readiness attestation` section; update the step-5 pointer wording
      and the "undischargeable readiness item" bullet to match.
- [x] 1.4 [req: readiness-attestation] Extend the self-review contract in
      `plugins/s/skills/plan/SKILL.md` (step 7) and
      `plugins/s/skills/plan/references/emission.md`: verify every
      attestation item in the staged `plan.md` carries evidence dot-points;
      an item without them is unmet and blocks installation.
- [x] 1.5 [req: readiness-attestation] Mirror the contract in
      `plugins/s/harness/bodies/plan.md`: step 5 prints the plain statements
      plus the path line, and step 6's `plan.md` bullet gains the
      `## Readiness attestation` section.
- [x] 1.6 [req: readiness-attestation, premise-evidence-in-attestation]
      Mirror the contract in `plugins/s/harness/references/plan.md`'s "The
      readiness bar": drop the table mandate, describe the printed plain form
      and the plan.md section, and route runnable-premise observations into
      the section's evidence.
- [x] 1.7 [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` so the cache snapshot refreshes.
