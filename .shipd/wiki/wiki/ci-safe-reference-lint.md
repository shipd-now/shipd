# ci-safe-reference-lint

Standing rule: a lint check that resolves a reference to a file **outside the
repository** (an `Initiative:` brief, a `PRD:` link — both workspace-hosted)
runs only when a workspace root is discoverable, and **skips silently in a
workspace-less checkout**. Rationale: repo lint runs as the required `ci`
check on bare GitHub runners, which never have a workspace — an erroring
check would pass locally and fail CI, so repo lint must never depend on
files outside the repository. The rule was set by the initiative reference
check and deliberately re-applied to the epic `PRD:` link after a mid-build
catch. Inside a discoverable workspace the checks stay strict: a dangling
reference is an error naming the expected path.

Backed by: verified/shipd-spec-format (epic-header-metadata),
verified/shipd-workspace (initiative-reference-resolution),
completed/epic-prd-link (plan ledger).
