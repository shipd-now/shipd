## MODIFIED Requirements

### Requirement: Robust source discovery and degradation
id: robust-source-discovery-and-degradation
base: e313862d1ffa

The tool SHALL locate the transcript directory from the working directory without
manual configuration, and SHALL degrade gracefully — reporting what it can and
noting the shortfall — if transcripts are missing or unreadable, rather than
failing the build. When the working directory's own transcript directory does
not exist and the working directory is a linked git worktree, the tool SHALL
resolve the worktree's main checkout root from the worktree's `.git` file
(`gitdir: <main>/.git/worktrees/<name>`) without invoking git, and SHALL use
the main checkout's transcript directory instead.

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

#### Scenario: Missing transcripts do not break the build
- **WHEN** the transcript files cannot be found or read
- **THEN** the tool emits a best-effort report with a clear note that token figures
  are unavailable, and exits without error
