## 1. Mermaid ladder

- [x] 1.1 [req: oracle-user-docs] In `docs/oracle.md`, replace the single
      fenced ASCII ladder diagram in the "The ladder" section (the bare ```
      fence between the paragraph ending "…comes up empty." and the paragraph
      beginning "That last arrow is the point") with a ```mermaid fence whose
      body is the verbatim content of `artefacts/oracle-ladder.mmd`. Change
      nothing else in the file.
- [x] 1.2 [req: oracle-user-docs] Verify: run
      `grep -rn '[─│┌┐└┘├┤┬┴▼]' docs/` and confirm it prints no matches
      (exit code 1), and run `grep -c '```mermaid' docs/oracle.md` and confirm
      it prints `1`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 42 | 13.2k |
| (no tool) | 0 | 2.4k |
| Read | 7 | 1.3k |
| Edit | 1 | 1.1k |
| Agent | 2 | 861 |
| **Total** | 52 | 18.8k |
