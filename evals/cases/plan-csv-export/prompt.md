/s:plan Add a `--csv` export flag to the report CLI in `src/report.py`.

Right now `report.py` prints a fixed, human-readable table of rows to stdout.
With `--csv`, it should instead print the same rows as comma-separated values
with a header line (`name,age,team`), one record per line, and no aligned
padding. The default (no flag) behavior is unchanged.

Plan this change end to end.
