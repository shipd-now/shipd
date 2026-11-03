# The /s:init settings sheet

The wizard prints this sheet once as plain response text and ends the turn.
It opens no AskUserQuestion. The rows follow the wizard-keys order. Each value
column shows the key's current value, or its default when no layer sets it.

## Bare wizard on a fresh project

```text
shipd setup: 9 settings. Each line shows the default.

  1  dir                  .shipd                   where shipd files live (a relative path)
  2  store_root           in the repo              or a store path, to keep files outside the repo
  3  pr-mode              auto                     auto | draft (draft stops at an open draft PR)
  4  autonomous-pipeline  default                  default | eco | basic
  5  memory_dir           /Users/me/.shipd-memory  your personal memory store (an absolute path)
  6  wiki_base            none                     or an absolute path to a base wiki
  7  voice                true                     true | false (the shipd writing voice in replies)
  8  guardrails           on                       on | false (false turns every rule off)
  9  constitution         add the starter          add | skip

Reply "ok" to accept every line.
To change lines, give the line number and the new value, e.g. "3 draft, 7 false".
```

## Bare wizard with some keys already set

Set keys move to an unnumbered `Already set (kept):` block above the numbered
lines, with their value and the file that sets them. The numbering covers the
unset lines only and starts at 1.

```text
shipd setup: 7 settings left. Each line shows the default.

Already set (kept):
  dir      .shipd   [/repo/.shipd-config.json]
  pr-mode  draft    [/repo/.shipd-config.json]

  1  store_root           in the repo              or a store path
  ...
```

When no unset key is left and no constitution line applies, the wizard prints
"nothing left to set up" instead of a sheet.

## Section run

`/s:init layout` or `/s:init config` numbers every key in that section, set or
not, with the current value shown. It has no `Already set` block and no
constitution line.

## The reply grammar

- `ok`, `yes`, `accept`, or an empty reply accepts every line as shown.
- `<n> <value>` changes line `n`. Separate several pairs with commas or new
  lines. Lines the reply does not name keep the shown value.
- A line number outside the sheet, or a reply that fits none of the forms
  above, triggers one re-print of the sheet with a one-line note naming the
  problem. A second unparseable reply stops the wizard with nothing written.
