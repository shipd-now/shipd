#!/bin/sh
# shipd installer — see README.md ("Install mode").
#
# POSIX sh, bash-3.2-safe (no arrays, no `set -u`), matching the shell
# precedent the constitution sets for `statusline.sh`. It downloads nothing
# itself: the two `claude plugin` steps do all the fetching, and the launcher
# below is written from a quoted heredoc so nothing in it is interpolated.

set -e

MARKETPLACE="shipd-now/shipd"
PLUGIN="s@shipd"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/shipd"

err() {
  printf 'Error: %s\n' "$1" >&2
}

# Abort before touching anything unless $1 is on PATH; $2 says how to get it.
require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "$1 is not on your \$PATH — $2"
    exit 1
  fi
}

# Run one `claude plugin` step, treating an already-present marketplace or
# plugin as success so a re-run is idempotent. $1 labels the step for the
# failure message; the rest are claude's arguments.
run_claude() {
  label="$1"
  shift
  if output=$(claude "$@" 2>&1); then
    if [ -n "$output" ]; then printf '%s\n' "$output"; fi
    return 0
  fi
  case "$output" in
    *[Aa]lready*)
      printf '%s\n' "$output"
      return 0
      ;;
  esac
  if [ -n "$output" ]; then printf '%s\n' "$output" >&2; fi
  err "$label failed: claude $*"
  exit 1
}

# Write the version-independent `shipd` launcher to $1.
#
# The heredoc delimiter below is quoted, so the body lands byte for byte and is
# the single source of truth for the launcher — the test suite extracts this
# same block rather than keeping a second copy.
write_launcher() {
  cat > "$1" <<'SHIPD_LAUNCHER_EOF'
#!/usr/bin/env python3
"""shipd — a version-independent front end for the installed plugin snapshot.

Claude Code installs the `s` plugin as a snapshot under
`~/.claude/plugins/cache/shipd/s/<version>/`, so any path pinned to one
version breaks at the next `claude plugin update`. This launcher resolves the
newest installed version at every invocation — dotted-integer ordering, so
0.6.10 beats 0.6.9 where a string sort would not — and replaces itself with
that snapshot's `bin/shipd`, which resolves its own engine scripts relative to
its location. Nothing here needs touching when a new version lands.

Stdlib-only Python 3, per the engine's constitution.
"""

import os
import sys

DEFAULT_CACHE = os.path.expanduser("~/.claude/plugins/cache/shipd/s")
FIX = "claude plugin install s@shipd"


def is_version(name):
    """Whether a cache entry names a dotted release (`0.6.10`). Anything else
    — a stray file, a `latest` alias — is not a snapshot and is ignored."""
    parts = name.split(".")
    return bool(parts) and all(part.isdigit() for part in parts)


def version_key(name):
    """A dotted version's comparison key, numeric part by numeric part."""
    return tuple(int(part) for part in name.split("."))


def newest_version(root):
    """The newest version directory under ``root``, or ``None`` when the cache
    root is absent, unreadable, or holds no version directory."""
    try:
        names = os.listdir(root)
    except OSError:
        return None
    versions = [name for name in names
                if is_version(name) and os.path.isdir(os.path.join(root, name))]
    if not versions:
        return None
    return max(versions, key=version_key)


def main(argv):
    root = os.environ.get("SHIPD_PLUGIN_CACHE") or DEFAULT_CACHE
    version = newest_version(root)
    if version is None:
        sys.stderr.write(
            "Error: no shipd plugin snapshot under %s — run `%s` (override "
            "the cache root with SHIPD_PLUGIN_CACHE)\n" % (root, FIX))
        return 1
    target = os.path.join(root, version, "bin", "shipd")
    try:
        os.execv(target, [target] + list(argv))
    except OSError as exc:
        sys.stderr.write(
            "Error: cannot run %s: %s — run `%s`\n" % (target, exc, FIX))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
SHIPD_LAUNCHER_EOF
  chmod +x "$1"
}

# --- install ---------------------------------------------------------------

require claude \
  "install Claude Code first (https://claude.com/claude-code), then re-run this installer"
require python3 \
  "install Python 3 (https://www.python.org/downloads/), then re-run this installer"

run_claude "registering the shipd marketplace" \
  plugin marketplace add "$MARKETPLACE"
run_claude "installing the s plugin" \
  plugin install "$PLUGIN"

mkdir -p "$BIN_DIR"
write_launcher "$LAUNCHER"

printf '%s\n' "Installed the ☕ shipd launcher at $LAUNCHER"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    printf '%s\n' \
      "Note: $BIN_DIR is not on your \$PATH. Add it to your shell profile:" \
      "  export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac
printf '%s\n' "Then run: shipd doctor"

# Claude Code leaves auto-update off for third-party marketplaces, so a fresh
# install would sit on this snapshot until someone updates by hand. Enabling it
# is the user's toggle to flip — this notice instructs, it never edits a
# settings file.
printf '%s\n' \
  "" \
  "Tip: turn on auto-update for the shipd marketplace so new versions arrive" \
  "on their own (Claude Code leaves it off for third-party marketplaces):" \
  "  in a session, run /plugin -> Marketplaces -> shipd and toggle it on" \
  "  or add \"autoUpdate\": true to the shipd entry under" \
  "  \"extraKnownMarketplaces\" in ~/.claude/settings.json" \
  "Updates are fetched shortly after a session starts and load in the next" \
  "session (or after /reload-plugins). To update by hand at any time, run:" \
  "  claude plugin update s@shipd"
