# Risk lenses

The skill reads this file when a risk lens trigger fires during review of the
diff.

Five triggers, four lenses: security splits into two triggers because exposure
and authorization are spotted by looking for different things. Each trigger
below names what to look for in the diff, one worked example of a finding
worth reporting, and one worked example of a reflex hit that is not — the line
between a real finding and a topic to muse about.

## Secret or credential exposure

Look for a new literal, log line, error message, fixture, or default value
carrying a key, token, password, connection string, or personal data.

- **Real finding.** A new config default embeds an API key literal
  (`api_key = "sk-live-..."`) instead of reading it from the environment or a
  secret store — the literal ships in every checkout and every log line that
  prints the config.
- **Reflex, not worth reporting.** A test fixture uses the well-known string
  `"password123"` as a local-only mock credential that is never sent anywhere
  and never resembles a real secret's shape.

**Severity floor: always `high`**, regardless of the reviewer's confidence
that the value is truly live — a leaked credential does not wait for
confirmation.

## Authorization boundary

Look for a new route, handler, background job, or query that reaches data or
performs an action without checking the caller's scope, role, or ownership
first.

- **Real finding.** A new `GET /admin/users/:id` handler loads the user record
  by `:id` alone, with no check that the caller is an admin or owns that
  record — any authenticated caller can read any user.
- **Reflex, not worth reporting.** An internal helper function takes a
  already-authorized `user` object as a parameter and performs no independent
  check, because the check already happened one layer up at the route that
  calls it.

**Severity floor: always `high`**, regardless of the reviewer's confidence —
an unguarded authorization boundary is always high.

## Unbounded work

Look for a loop, recursion, batch, or fan-out whose iteration count or size is
driven by user input or external data with no cap.

- **Real finding.** A new endpoint loads `request.body.ids` and issues one
  database query per id with no limit on the array's length — a caller can
  submit ten thousand ids and exhaust the connection pool.
- **Reflex, not worth reporting.** A loop iterates over a config-defined list
  of five known regions, fixed at deploy time and never user-influenced.

Rates on the existing high/medium/low rubric — no floor.

## Resource release

Look for a newly opened file handle, socket, lock, connection, or transaction
that is not released on every exit path, including the error path.

- **Real finding.** A new function opens a database transaction, then returns
  early on a validation failure before the transaction is committed or rolled
  back, leaking the connection back to the pool in an open state.
- **Reflex, not worth reporting.** A short-lived helper opens a file using a
  context manager (`with open(...) as f:`) that already guarantees the handle
  closes on every exit path, including exceptions.

Rates on the existing high/medium/low rubric — no floor.

## Migration reversibility

Look for a new schema migration, data backfill, or destructive data operation
with no down-migration, no backup step, or no way to recover the prior state.

- **Real finding.** A new migration drops a column that still holds live data
  in production, with no down-migration and no backfill into a replacement
  column first — the data is gone the moment the migration runs.
- **Reflex, not worth reporting.** A migration adds a new nullable column with
  no default, which is additive and trivially reversible by dropping the same
  column.

Rates on the existing high/medium/low rubric — no floor.
