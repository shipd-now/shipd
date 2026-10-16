<!-- doc-type: how-to -->

# Episode 4: PRDs and guardrails

## Introduction

A feature that starts without a settled problem statement drifts, and a
convention that lives only in a prompt scrolls out of attention. This episode
shows two fixes. A PRD captures the problem, the users, and the success
criteria before anyone plans a change. A guardrail blocks an unwanted line
before it lands in a file. The episode is for engineers who start features
and want the code to follow house rules.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Spec authoring and pressure testing |
| Runtime | 5 minutes |
| Prerequisites | A workspace; episodes 1 to 3 |
| Commands shown | `shipd workspace init`, `/s:prd`, a rule file in `.shipd/rules/` |

## Script

### 0:00–0:45 Why settle the problem first

**On screen:** A diagram of the hierarchy: initiative, PRD, epic, change.
The initiative and PRD boxes sit in a workspace. The epic and change boxes
sit in a repository.

**Narration:** Before anyone decomposes a feature, someone settles what
problem it solves and for whom. shipd calls this the discover phase. The
result is a PRD, a document that sits above epics. Every link in the
hierarchy is optional, so a PRD can stand alone.

### 0:45–2:00 Interview a PRD into existence

**On screen:** A terminal runs `shipd workspace init` for a new workspace.
Then the presenter types `/s:prd notifications for documents shared with me`.
The session searches the workspace, announces a tier, and asks the first
question.

**Narration:** A PRD lives in the workspace, not in the repository. So you
create the workspace first. The command `/s:prd` is an interrogation, not a
form. It reads the workspace and the repository, then asks one template
section per round. It announces a tier: basic, standard, or comprehensive.

### 2:00–3:00 Install the PRD and hand off

**On screen:** The final round ends. The engine installs the document under
the workspace's `prds` directory. The session prints a pointer to `/s:epic`.

**Narration:** The engine validates the document and installs it. A PRD has
no branch and no pull request, because it lives outside the repository. The
skill hands off to `/s:epic` and stops. It never decomposes the PRD itself.

### 3:00–4:15 Block a line before it lands

**On screen:** The presenter creates `.shipd/rules/no-bare-except.md` with a
`pattern`, a message, and the default `deny` mode. A model edit adds a bare
`except:` line. The hook blocks the edit and shows the rule's message.

**Narration:** A guardrail is a markdown rule file. Its frontmatter holds a
regex, and its body tells the model what to do instead. The hook matches
added lines around every edit and write. In deny mode, the hook blocks the
call, and the model retries. The rule file lives in the repository, so the
whole team gets it.

### 4:15–5:00 Remind instead of block

**On screen:** The presenter changes the rule to `mode: remind`. The edit
stands, and a reminder appears once for the session. A table lists the three
built-in rules.

**Narration:** In remind mode, the edit stands and the model gets a note. A
reminder fires once per session unless you set a cooldown. Three built-in
rules ship with the plugin. They catch comments that narrate the edit.

## Takeaways

- A PRD records the problem and the success criteria in the workspace,
  before any epic exists.
- `/s:prd` interviews you section by section and installs a validated
  document.
- A guardrail rule file blocks or flags a line at edit time, so a prompt
  need not repeat the convention.

## Next

Episode 5 turns an approved PRD into an epic with
[Epics and `/s:epic-grill`](05-epics-and-epic-grill.md).

## Sources

- [PRDs](../../prd.md)
- [Guardrails](../../guardrails.md)
- [Workspaces](../../workspaces.md)
