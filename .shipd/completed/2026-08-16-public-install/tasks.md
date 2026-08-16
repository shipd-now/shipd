## 1. Launcher

- [x] 1.1 [req: cache-launcher] Add failing tests in
      `plugins/s/skills/build/tests/test_install.py`: with
      `SHIPD_PLUGIN_CACHE` pointing at a fake cache holding `0.6.9` and
      `0.6.10` (each holding a stub shipd binary echoing its version), the
      launcher executes `0.6.10`'s binary; arguments and exit code pass
      through; an empty cache root exits nonzero naming
      `claude plugin install s@shipd`; a non-version directory name is
      ignored.
- [x] 1.2 [req: cache-launcher] Author the python3 launcher body (inside
      `install.sh` as a quoted heredoc, plus the same body extracted for the
      tests): resolve cache root from `SHIPD_PLUGIN_CACHE` or the default,
      pick the newest dotted-integer version directory, `os.execv` the shipd binary inside that snapshot. Run the 1.1 tests green.

## 2. Installer

- [x] 2.1 [req: install-script] Add failing tests: `install.sh` under a temp
      `HOME` with a stub `claude` recording argv performs the marketplace
      add and plugin install, writes an executable `~/.local/bin/shipd`,
      prints a PATH hint when `~/.local/bin` is absent from PATH, exits
      nonzero with no launcher when `claude` is missing, and re-runs
      idempotently when the stub reports already-present.
- [x] 2.2 [req: install-script] Implement `install.sh` at the repo root
      (POSIX sh, bash-3.2-safe, no arrays): prerequisite checks, the two
      tolerant `claude` invocations, launcher write + `chmod +x`, PATH
      hint. Run the 2.1 tests green.
- [x] 2.3 [req: install-script] Add `bash -n install.sh` to the CI shell
      syntax checks step in `.github/workflows/ci.yml`.

## 3. Docs

- [x] 3.1 [req: install-mode-docs] Rewrite `README.md`'s installation
      section: install mode first (the `curl | sh` one-liner and the two
      `claude plugin` commands, the launcher's `~/.local/bin` location),
      then the existing clone/symlink text under an explicit dev-mode
      heading, keeping the never-symlink-the-cache warning.

## 4. Verify

- [x] 4.1 [req: *] Run `plugins/s/skills/build/tests/` with no `textual`
      installed; green.
