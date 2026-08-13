/s:plan Add a `--version` flag to the report CLI in `src/report.py`.

When invoked with `--version`, the command should print the tool's version
string (`report 1.0.0`) to stdout and exit without printing the table. This is
a new, self-contained capability unrelated to the existing table-printing
behavior, which stays exactly as it is.

Plan this change end to end.
