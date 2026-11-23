# Report CLI flags

Every flag on the `report` CLI is a long-form `--name` flag with no
single-letter alias, so a script that calls the tool reads the same as the
help text.

A flag that takes a value accepts it as the next argument, never joined to
the flag with an equals sign.
