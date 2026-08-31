## 1. Vertical overview layout

- [x] 1.1 [req: what-is-overview-layout] In `docs/what-is-shipd.md`, change
      the mermaid fence's first body line from `flowchart LR` to
      `flowchart TD`. Nothing else inside the fence changes.
- [x] 1.2 [req: what-is-overview-layout] In `docs/what-is-shipd.md`, move the
      whole paragraph beginning "Today shipd builds itself —" and ending
      "… without watching it type." from before the `## How it fits together`
      heading to after the closing ``` of the mermaid fence, keeping the
      paragraph text byte-identical, with one blank line between the fence and
      the paragraph and no trailing prose after it.
- [x] 1.3 [req: what-is-overview-layout] Verify: `grep -c 'flowchart TD'
      docs/what-is-shipd.md` prints `1`; `grep -c 'flowchart LR'
      docs/what-is-shipd.md` prints `0`; and the line number
      `grep -n 'Today shipd builds itself' docs/what-is-shipd.md` reports is
      greater than the line number of the fence's closing ``` (the last line
      matching `grep -n '^```$' docs/what-is-shipd.md`).

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 40 | 14.7k |
| (no tool) | 0 | 2.6k |
| Edit | 3 | 1.1k |
| Read | 7 | 811 |
| Agent | 2 | 648 |
| **Total** | 52 | 19.9k |
