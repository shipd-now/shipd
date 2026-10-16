# statusline-context-colour
Status: verified
Planned-at: e125037ba98f7cfbfe23e735250d1849a2b4bc6b
Gated-hash: a139ac845323

## Idea

Color the statusline's context-usage segment so its level reads at a glance:
blue while usage is comfortable, shading through orange to dark red as the
context window fills.

### Motivation

The context bar renders uncolored, so `██░░ 50%` and `████ 97%` look alike
at a glance. The user wants it blue like the change name, turning orange
above 50%, red above 75%, darker red above 90%, and dark red above 95%.

### Details

Thresholds apply to the clamped integer percentage: ≤ 50 light blue
(`\033[94m`), > 50 orange (`208`), > 75 red (`196`), > 90 darker red (`160`),
> 95 dark red (`124`). Only the bar and its percentage are colored; the
` · ` separators stay uncolored, as for every other segment.

### Non-goals

- No color configuration; the thresholds are fixed.
- No change to the directory or spec segments' colors.

## Implementation

- **Script.** In `plugins/s/integrations/statusline.sh`, where `ctx_seg` is
  built from `bar` and `ctx_pct`, pick `ctx_color` with a bash 3.2 `if/elif`
  chain from the highest threshold down: `> 95` → `$'\033[38;5;124m'`,
  `> 90` → `160`, `> 75` → `196`, `> 50` → `208`, else `$NAME_COLOR`. Set
  `ctx_seg="${ctx_color}${bar} ${ctx_pct}%${RESET}"`. The segment stays
  empty when no percentage is parsed, so no color codes leak.
- **Tests.** In `plugins/s/skills/build/tests/test_statusline.py`, assert on
  the raw (ANSI-preserving) output for 50/51/76/91/96 and on the boundaries
  75 and 95 staying in the lower band; existing tests strip ANSI and stay
  green.
- **Version.** Bump `plugins/s/.claude-plugin/plugin.json` `0.6.308` →
  `0.6.309`.

## Readiness attestation

### Problem and motivation

The context bar carries no color, so its level is hard to read at a glance.

Evidence:

- `statusline.sh` sets `ctx_seg="${bar} ${ctx_pct}%"` with no color code.
- The user asked for blue, then orange >50, red >75, darker red >90, dark
  red >95.

### Scope and non-goals

Only the context segment's color changes.

Evidence:

- In scope: the `ctx_seg` assignment in `statusline.sh` and its tests.
- Out of scope: the spec and directory segments, configuration.

### Affected capabilities and files

One capability, one modified requirement.

Evidence:

- `statusline`: `statusline-rendering` (base ba206a732d2d).
- Files: `plugins/s/integrations/statusline.sh`,
  `plugins/s/skills/build/tests/test_statusline.py`,
  `plugins/s/.claude-plugin/plugin.json`.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Thresholds and color names: stated by the user.
- Blue = the existing change-name blue `\033[94m`; xterm-256 indices for
  the reds and orange: chosen to match the script's existing xterm-256 use
  in the live-run dot ramp.
