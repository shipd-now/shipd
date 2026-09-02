## MODIFIED Requirements

### Requirement: Robust source discovery and degradation
id: robust-source-discovery-and-degradation
base: 05f4e761ecbc

The tool SHALL locate the transcript directory from the working directory
without manual configuration, and SHALL degrade gracefully — reporting what it
can and noting the shortfall — if transcripts are missing or unreadable,
rather than failing the build. When the working directory's own transcript
directory does not exist and the working directory is a linked git worktree,
the tool SHALL resolve the worktree's main checkout root from the worktree's
`.git` file (`gitdir: <main>/.git/worktrees/<name>`) without invoking git, and
SHALL use the main checkout's transcript directory instead.

When neither the working directory's own transcript directory nor the main
checkout's exists, the tool SHALL probe the path slugs of the resolved project
root's ancestor directories, nearest first, and SHALL select from the first
ancestor transcript directory that yields a match. Within an ancestor's
transcript directory, the tool SHALL select the most recently modified session
transcript whose trailing records carry a working directory at or under the
resolved project root, and SHALL NOT select a transcript whose trailing
working directory lies outside that root. Where a session id is supplied
explicitly, the tool SHALL instead select that session's transcript from the
first candidate directory that holds it, without a working-directory check.

#### Scenario: Transcript directory derived from the project path
- **WHEN** the tool runs inside the project with no explicit path override
- **THEN** it resolves the session transcript directory from the project path and
  selects the active session's transcript

#### Scenario: Worktree build falls back to the main checkout's transcripts
- **GIVEN** a session launched from the main checkout that runs a build inside
  `.worktrees/<change>`
- **WHEN** the tool runs from the worktree and no transcript directory exists
  for the worktree's own path slug
- **THEN** it resolves the main checkout root from the worktree's `.git` file
  and reads the session transcripts from the main checkout's slug

#### Scenario: A session launched inside the worktree is unaffected
- **WHEN** the tool runs in a directory whose own transcript directory exists
- **THEN** that directory is used and no worktree resolution is attempted

#### Scenario: Session launched from an ancestor directory is found
- **GIVEN** a session launched from a parent directory of the project that has
  since changed into the project, so its transcript lives under the parent
  directory's path slug
- **WHEN** the tool runs in the project and no transcript directory exists for
  the project's own slug or its main checkout's
- **THEN** it selects that session's transcript from the ancestor directory's
  slug and reports its token usage

#### Scenario: A foreign session in the ancestor directory is skipped
- **GIVEN** an ancestor slug directory whose newest transcript belongs to a
  session whose trailing working directory lies in a different project
- **WHEN** the tool falls back to that ancestor's transcript directory
- **THEN** the foreign transcript is not selected, and an older transcript
  whose trailing working directory lies within the resolved project root is
  selected instead

#### Scenario: Missing transcripts do not break the build
- **WHEN** the transcript files cannot be found or read
- **THEN** the tool emits a best-effort report with a clear note that token figures
  are unavailable, and exits without error
