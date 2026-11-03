#!/usr/bin/env bash
# sandbox-run.sh: run one quoted command under the shipd sandbox env (fake
# HOME, XDG dirs, TMPDIR, scrubbed credentials). All logic lives in
# sandbox_run.py beside this shim.
exec python3 "$(cd "$(dirname "$0")" && pwd)/sandbox_run.py" "$@"
