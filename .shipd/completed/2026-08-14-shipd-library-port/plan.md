# shipd-library-port
Status: verified
Epic: shipd-port
Theme: spec-engine

## Idea

Port shipd's spec library to `.shipd/` in the shipd repo — the master
capabilities with their `am-*` → `shipd-*` renames, the archived changes, the
epics, and the config — and prove it with a clean lint and metrics parity.

### Motivation

`metrics.py` and the delivery board derive throughput, cycle time, and the
forecast from the `completed/` archive, so the history must come across *and*
parse under the new names (`.shipd/epics/shipd-port/epic.md`, Decisions). A ported
engine with no library reads nothing.

### Details

- Run `port.py apply --include .shipd/ --include .shipd-config.json` against shipd at
  a pinned ref.
- Confirm the sixteen `am-*` capability directories landed as `shipd-*` under
  both `verified/` and every archived change's `specs/`.
- Confirm `openspec/` and `.shipd/` did not come across.
- Prove correctness structurally: `spec_lint.py` clean over the whole library, and
  `metrics.py` deriving the same figures in shipd as in shipd.

Affected capabilities: `shipd-port` (added). Impact: the shipd repo (`.shipd/`,
`.shipd-config.json`); shipd unchanged.

### Non-goals

- No editing of archived content beyond the rename the tool applies. Completed
  changes are immutable (`.shipd/constitution.md`, Workflow discipline); the port
  rewrites their namespace tokens and nothing else.
- No `openspec/` — dropped, per the epic.
- No new or removed capabilities. The library that lands is the library that
  existed at the pinned ref, renamed.
- No brand copy in `.shipd/README.md` or `constitution.md` beyond the token map's
  substitutions; member 5 owns the prose.

## Implementation

- **Same pinned-ref discipline as the engine port.** `apply` runs with an explicit
  `--ref <sha>` recorded in the PR body. Ideally the same sha as
  `shipd-engine-port` used, so engine and library describe one coherent snapshot
  of shipd; where shipd moved between the two members, the later sha is
  used and the difference noted.

- **Capability renames are asserted by enumeration, not spot-checked.** The tool
  derives the rename set from `.shipd/verified/`; this member independently lists
  shipd's `am-*` capability directories at the ref and asserts a `shipd-*`
  counterpart exists in shipd for each — and that no `am-*` directory survives
  anywhere under `.shipd/`. A spot check would miss exactly the long-tail
  capability nobody remembers.

- **Lint over the whole library is the structural proof.** `spec_lint.py` with no
  argument validates the master library, and it is what catches a rename that
  broke a delta's `specs/<capability>/` path or a `[req:]` reference. Rejected:
  eyeballing a sample of the 150 archived changes — the failure mode here is a
  single stale cross-reference, which reading cannot reliably find.

- **Metrics parity is the semantic proof.** A library can lint clean and still
  have lost archive entries — a dropped `completed/` directory changes throughput
  silently. So `metrics.py` is run in both repos over the same window and the
  figures compared. Any divergence means a file did not cross, and blocks the
  member.

- **`.shipd-config.json` ports to `.shipd-config.json` with its keys intact.**
  `valid_themes` and the `build.video_speakers` list carry over unchanged; only
  the filename changes. The workspace-declaring layer lives in shipd's parent
  directory and is *not* ported — shipd is a standalone repo until a workspace
  chooses to include it.

- **The vestigial `.shipd/state.json` is dropped, not renamed.** It holds an
  OpenSpec-era `current_spec` marker with no live reader; the tool's exclusion
  list already covers it, and this member asserts the absence rather than
  assuming it.

Risk: the epic file for `shipd-port` itself ports across, so shipd's library will
contain the epic describing its own creation. That is intended — it is the record
of how the repo came to exist — but its `Status:` will read whatever shipd's
copy read at the pinned ref, which may lag. Member 7 re-derives it.
