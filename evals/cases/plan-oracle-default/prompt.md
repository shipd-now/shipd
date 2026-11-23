/s:plan Add a `--sort` flag to the report CLI in `src/report.py`.

With `--sort <column>`, where the column is `name`, `age`, or `team`, the
command prints the same table with its rows in ascending order of that column.
The header line and the column padding stay exactly as they are, and without
the flag the output is unchanged.

`--sort` given on its own, with no column after it, must also work. Which
column it sorts by then has not been decided yet.

Plan this change end to end.
