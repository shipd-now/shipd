<!-- doc-type: how-to -->

# Personal memory

**Personal memory** is one wiki that belongs to you, not to a workspace. It
lives at `<memory_dir>/wiki`, by default `~/.shipd-memory/wiki`. It holds one
`memory-<subject>` page per durable preference, such as an editor choice or a
diagram style.

The [oracle](oracle.md) reads your personal memory first, before any workspace
store. A preference you capture once therefore shapes every repository you
work in.

The store is a single durable store. It has no base store beneath it, and no
skill promotes its pages anywhere.

## When to use it

Capture a preference here when it is about you: a tool, a tone, or a
formatting habit. Knowledge about the workspace, such as a team convention or
an engineering position, belongs in the [wiki](wiki.md) instead.

- **`/s:remember`** — capture a new preference, or update one.
- **`/s:memory`** — list the preferences the store holds.
- **`/s:forget`** — remove one preference.

Each oracle consultation, from [`/s:plan`](plan.md) or [`/s:ask`](oracle.md), reads your memory first.

## How to run it

### Capture a preference

Pass the preference as the argument, or run the skill bare:

```sh
/s:remember prefers vim over vscode
/s:remember
```

With no argument, the skill proposes the standing preferences you stated in
this session. It runs these steps:

1. **Resolve the store.** On first use, it scaffolds the store.
   [`/s:init memory`](customise.md) scaffolds it ahead of time.
2. **Reconcile.** It compares each candidate with the existing `memory-*`
   pages. It classifies each one as **add** (a new page), **update** (a
   changed page), or **skip** (a duplicate).
3. **Confirm.** It lists each candidate with its classification, its slug, and
   its statement. It writes nothing until you type a go-ahead. You can also
   prune or amend the set.
4. **Write once.** It stages the touched pages and installs them in one write.
   The write runs the wiki lint and restores the store on any finding.

The skill also offers to back the store with git, one typed round per step.
None of these steps runs without your consent:

- **`git init`** — on the first run, the skill offers to initialize
  `<memory_dir>` as a git repository. Each capture then commits locally, unless `SHIPD_STORE_AUTOCOMMIT=0` is set in the environment.
- **The remote** — the skill offers to create a private `shipd-memory`
  repository through `gh` and wire it as `origin`.
- **The push** — the skill offers a confirmed push, separately from the
  remote. On later runs, it offers a push whenever the remote falls behind.

When `gh` is absent or you decline, the skill prints the manual commands:

```sh
gh repo create shipd-memory --private
git -C <memory_dir> remote add origin <url>
git -C <memory_dir> push -u origin <branch>
```

A failed remote or push never fails the capture. The local commit stands. The
engine itself never pushes, pulls, or fetches.

### List your memories

```sh
/s:memory
```

The skill prints each `memory-*` page with its summary. It is read-only: it
writes nothing, asks nothing, and never scaffolds a missing store.

### Forget a memory

Describe the memory in your own words:

```sh
/s:forget my editor preference
```

The skill runs these steps:

1. It searches the `memory-*` pages for the description.
2. When several pages match, it lists them and asks you to pick one.
3. It asks you once to confirm. The default answer keeps the page.
4. Only on your yes, it removes the page and its index entry.

When nothing matches, the skill removes nothing.

## Reference

### The page shape

```
# memory-<subject>

<one-line preference statement>

- Origin: <invoking-repo>
- Captured: <YYYY-MM-DD>
```

The `<subject>` is kebab-case, such as `memory-editor-choice`. `Origin:` names
the repository the capture ran from.

### The skills

| skill | what it does | writes |
| --- | --- | --- |
| `/s:remember [preference]` | Captures or updates preferences after a typed go-ahead. | yes |
| `/s:memory` | Lists the `memory-*` pages. | no |
| `/s:forget <description>` | Removes one page after one confirmation. | yes |

### The store report

[`shipd wiki --personal`](wiki.md) reports the personal store: its root, page count,
coverage, and last log entry.

The `memory_dir` key sets the store's root; see
[Customising shipd](customise.md).
