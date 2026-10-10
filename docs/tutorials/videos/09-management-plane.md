<!-- doc-type: how-to -->

# Episode 9: The management plane (commercial)

## Introduction

Engineering managers need to see where a feature stands without reading every
repository. This episode shows the management plane, a dashboard over
team-shared workspaces. It is the one commercial part of the series. Episodes
1 to 8 cover open-source shipd, and this episode covers what the commercial
product ships today. It is for managers and for engineers who report to them.

## At a glance

| Item | Detail |
|---|---|
| Roadmap group | Verification and governance |
| Runtime | 5 minutes |
| Prerequisites | A team-shared workspace; episodes 1 to 8 |
| Commands shown | None; the episode shows the `shipd-app` dashboard |

## Script

### 0:00–0:50 The open-source line

**On screen:** A slide splits the series in two. Episodes 1 to 8 sit under
"open source". Episode 9 sits under "commercial".

**Narration:** Everything so far runs on open-source shipd. The docs describe
the plugin, the engine, and the workflows, and you can use them freely. The management
plane is different. It is a commercial product that reads what shipd already
writes to git.

### 0:50–2:10 A read-only delivery view

**On screen:** The dashboard opens on a workspace. A tree shows initiatives,
then epics, then member changes. Each member change carries a lifecycle
status and a gate verdict.

**Narration:** The dashboard is a read-only delivery view for engineering
managers. It covers team-shared workspace repos. It follows the hierarchy
from initiatives to epics to member changes. It derives every status from
git, so it never becomes a second source of truth.

### 2:10–3:20 Knowledge stays in git

**On screen:** The presenter opens a wiki page in the browser, edits it, and
saves. A split view shows the resulting commit in the workspace repo.

**Narration:** A wiki edit saved in the browser becomes a git commit in the
workspace repo. The service lints the edit through the engine's wiki emit
before it pushes. If a teammate edits the same page first, the client reloads
and reapplies your change.

### 3:20–4:20 Comments live beside the work

**On screen:** The presenter selects text in an epic and adds a comment. The
file tree shows a `.comments.jsonl` file under `.shipd/comments/`.

**Narration:** Comments on workspace pages also live in git. Each page has
one append-only file, so two people can comment on the same page without a
merge conflict. A manager reads the thread. An engineer reads the same thread
in the repo.

### 4:20–5:00 What ships and what is direction

**On screen:** A two-column slide. The left column lists what the dashboard shows today. The right column carries the heading "Direction" and four items: executive dashboards, cross-repo drift tracking for architecture, compliance reporting, and org-wide policy rollouts.

**Narration:** The left column is what the product ships today. The right column is direction, not shipped features. Executive dashboards, cross-repo drift tracking for architecture, compliance reporting, and org-wide policy rollouts are where the management plane is heading.

## Takeaways

- Episodes 1 to 8 cover open-source shipd, and the management plane is
  commercial.
- The dashboard is a read-only delivery view that derives its status from
  git.
- Wiki edits and comments land in the workspace repo as git commits.

## Next

Return to the [series overview](index.md) to pick an episode to rewatch.

## Sources

- The `shipd-app` repository README
- [Workspaces](../../workspaces.md)
- [Sharing a workspace with a team](../../workspaces/teams.md)
