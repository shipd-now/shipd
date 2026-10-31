# /s:init wizard keys

The wizard's steps, in order, and the dialog each key gets. "Default" is the
option listed first when no layer declares the key (when one does, its current
value is listed first instead). "Writes on default" says whether choosing the
default runs `shipd config set` (Q5): a key whose default is the key's absence
writes nothing when the default is chosen.

| Step | Section | Key | Options (default first) | Writes on default |
| --- | --- | --- | --- | --- |
| 1 Where files live | `layout` | `dir` | `.shipd`; Other (a relative path) | yes, `.shipd` |
| 1 Where files live | `layout` | `store_root` | keep files in the repo; Other (a store path) | no |
| 2 How changes ship | `config` | `pr-mode` | `auto`; `draft` | yes, `auto` |
| 2 How changes ship | `config` | `autonomous-pipeline` | `default`; `eco`; `basic` | yes, `default` |
| 3 Personal stores | `config` | `memory_dir` | `$HOME/.shipd-memory` expanded; Other (an absolute path) | yes |
| 3 Personal stores | `config` | `wiki_base` | no base wiki; Other (an absolute path) | no |
| 4 Session behaviour | `config` | `voice` | `true`; `false` | yes, `true` |
| 4 Session behaviour | `config` | `guardrails` | keep every rule on; `false` (all off) | no |
| 5 Constitution | wizard only | `constitution.md` | add the starter; skip | n/a (file, not config) |

Step 1 ends by running `spec_status.py init`, which creates the folders the
chosen `dir` and `store_root` resolve to. The value passed to `shipd config
set` is the option's literal (`false`, `auto`, a path); `shipd config set`
parses JSON first and falls back to a plain string (config-control Q3), so no
quoting is needed.

On-demand sections, never run by the bare wizard:

| Section | What it runs |
| --- | --- |
| `workspace` | `shipd workspace`; when none resolves, one path dialog, then `spec_status.py workspace-init <path>` |
| `wiki` | `spec_status.py wiki-init` |
| `memory` | `spec_status.py wiki-init --personal` |
| `hooks` | hands off to `/s:worktree-hooks` |
| `gate` | hands off to `/s:gate` |
