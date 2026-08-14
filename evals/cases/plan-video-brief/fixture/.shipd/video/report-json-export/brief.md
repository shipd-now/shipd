# Add JSON export to the report CLI
Video: Screen Recording 2026-08-01 at 10.15.00 am.mov
Bundle: report-json-export

## Intents

### Add a `--json` export flag to the report CLI

Dana asks for a `--json` flag on `report.py` that prints the same rows as a
JSON array of objects (`name`, `age`, `team`) instead of the padded table, so
the output can be piped into other tools. The default (no flag) behavior
stays exactly as it is [1].

## Sources

1. [00:00:42] "Can we get a --json flag that just dumps the rows as a
   JSON array instead of this padded table? Everything else can stay the
   same."
