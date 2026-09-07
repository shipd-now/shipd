## 1. The practical-examples section

- [x] 1.1 [req: workspaces-doc-examples] Append
      `## 10. Practical examples: multi-workspace repos` to
      `docs/workspaces.md`, written exactly to the six-part frame in
      `plan.md`'s `## Implementation` (intro; Shape A sibling workspaces with
      diagram and setup; Shape B nested jobs with diagram, setup, and a §6
      cross-link; what-lives-where table(s); using-either-option flow with
      plain `git clone`; pros/cons table with the when-to-pick-which and
      access-control closing notes). Match the surrounding guide's diagram
      style, heading register, and `shipd`-binary command convention.
- [x] 1.2 [req: workspaces-doc-examples] Verify the section against its
      contract: confirm `grep -n "spec_status.py" docs/workspaces.md` matches
      nothing between the `## 10.` heading and end-of-file, confirm both
      shape diagrams and the storage table(s) are present, and confirm the
      section's internal links (`#6-nesting-job-workspaces`,
      `#8-sharing-a-workspace-with-a-team`) resolve to real headings in the
      file.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 49 | 12.7k |
| (no tool) | 0 | 3.8k |
| Agent | 2 | 660 |
| Read | 6 | 352 |
| Write | 1 | 9 |
| **Total** | 58 | 17.5k |
