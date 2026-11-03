#!/usr/bin/env python3
"""sandbox_run: run one command under a sandbox env, so a validator or
sub-agent exercising ``gh``, ``git`` or project scripts cannot reach the real
user state (validator-sandbox).

The leak check accepts the repo root in every home form (the resolved path and
its path under the literal and resolved real HOME, so a symlinked HOME works),
and the env scrub keeps the toolchain locator variables (``PYENV_ROOT`` and
kin), deriving an unset one from a ``<home>/<dir>/shims`` entry on ``PATH``.

Usage (via the ``sandbox-run.sh`` shim):
    sandbox-run.sh '<command>'   run ``bash -c '<command>'`` in the sandbox
    sandbox-run.sh --reset       delete the sandbox root, print it
    sandbox-run.sh --print-root  print the sandbox root, create nothing

The root is ``<tmp>/shipd-sandbox/<id>`` (per repo, persistent across calls)
holding ``home/``, ``tmp/`` and ``state/``. Exit codes: 2 for a usage error or
a leak refusal, 3 for a sandbox set-up failure; otherwise the command's own.
Stdlib only."""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import spec_common  # noqa: E402

TOKEN_VARS = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN",
              "GITHUB_ENTERPRISE_TOKEN")

# Locator variables the scrub keeps even when they name the real HOME.
TOOLCHAIN_VARS = ("PYENV_ROOT", "RBENV_ROOT", "ASDF_DATA_DIR", "VIRTUAL_ENV",
                  "CONDA_PREFIX")
# Locators derivable from a ``<home>/<dir>/shims`` PATH entry when unset.
SHIM_ROOTS = {"PYENV_ROOT": ".pyenv", "RBENV_ROOT": ".rbenv",
              "ASDF_DATA_DIR": ".asdf"}


def die(code, message):
    sys.stderr.write("sandbox-run: %s\n" % message)
    sys.exit(code)


def repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True,
            text=True)
        if out.returncode == 0 and out.stdout.strip():
            return os.path.realpath(out.stdout.strip())
    except OSError:
        pass
    return os.path.realpath(os.getcwd())


def home_forms(home):
    forms = []
    for form in (home, os.path.realpath(home) if home else home):
        form = form.rstrip("/") if form else form
        if form and form not in forms:
            forms.append(form)
    return forms


def repo_home_forms(repo, forms, real_home):
    """The resolved repo root first, then, when it sits under the resolved
    real HOME, its path under each home form."""
    out = [repo]
    rhome = os.path.realpath(real_home).rstrip("/") if real_home else ""
    if rhome and (repo == rhome or repo.startswith(rhome + os.sep)):
        suffix = repo[len(rhome):]
        for form in forms:
            cand = form + suffix
            if cand not in out:
                out.append(cand)
    return out


def _is_repo_ref(text, start, repo_forms):
    """True when ``text`` at ``start`` begins with a repo-root form and the
    next character ends that path (not a sibling such as ``<repo>-other``)."""
    for repo in repo_forms:
        if not text.startswith(repo, start):
            continue
        end = start + len(repo)
        if (end >= len(text) or text[end] == os.sep or text[end].isspace()
                or text[end] in "'\";):"):
            return True
    return False


def outside_repo_home_ref(text, forms, repo):
    """Return the first occurrence of a real-HOME path in ``text`` whose
    continuation does not begin with a repo-root form (``repo`` is a list of
    forms), else None."""
    for form in forms:
        start = text.find(form)
        while start != -1:
            if not _is_repo_ref(text, start, repo):
                return text[start:start + len(form) + 24].split()[0]
            start = text.find(form, start + 1)
    return None


def main(argv):
    if argv[:1] in (["--reset"], ["--print-root"]) and len(argv) == 1:
        mode = argv[0]
        command = None
    elif len(argv) == 1 and not argv[0].startswith("--"):
        mode = "run"
        command = argv[0]
    else:
        die(2, "pass the command as one quoted string")

    real_home = os.environ.get("HOME", "")
    forms = home_forms(real_home)
    repo = repo_root()
    repo_forms = repo_home_forms(repo, forms, real_home)
    # TMPDIR is honoured as given: gettempdir() silently falls back to
    # /tmp when TMPDIR is unusable, which would hide a create failure.
    base = os.environ.get("TMPDIR") or tempfile.gettempdir()
    ident = hashlib.sha256(repo.encode()).hexdigest()[:12]
    root = os.path.join(base, "shipd-sandbox", ident)

    if mode == "--print-root":
        print(root)
        return 0
    if mode == "--reset":
        shutil.rmtree(root, ignore_errors=True)
        print(root)
        return 0

    real_root = os.path.realpath(root)
    for form in forms:
        if real_root == form or real_root.startswith(form + os.sep):
            die(3, "sandbox root %s is inside the real HOME" % root)
    try:
        for sub in ("home", "tmp", "state"):
            os.makedirs(os.path.join(root, sub), exist_ok=True)
    except OSError as exc:
        die(3, "cannot create sandbox root %s: %s" % (root, exc))
    sys.stderr.write("sandbox-run: root=%s\n" % root)
    sys.stderr.flush()

    match = outside_repo_home_ref(command, forms, repo_forms)
    if match:
        die(2, "command names the real HOME outside the repo: %s" % match)

    try:
        config, provenance = spec_common.resolve_config(repo)
    except Exception as exc:  # a malformed config must not run unsandboxed
        die(3, "cannot read config: %s" % exc)
    if "sandbox" in config:
        import config_registry
        try:
            config_registry.REGISTRY["sandbox"].validate(
                config["sandbox"], provenance.get("sandbox"))
        except Exception as exc:
            die(3, "invalid sandbox config: %s" % exc)
    declared = config.get("sandbox")
    declared = declared if isinstance(declared, dict) else {}

    env = {}
    for name, value in os.environ.items():
        if name in TOKEN_VARS:
            continue
        if (name != "PATH" and name not in TOOLCHAIN_VARS
                and outside_repo_home_ref(value, forms, repo_forms)):
            continue
        env[name] = value
    path_entries = env.get("PATH", "").split(os.pathsep)
    for name, dirname in SHIM_ROOTS.items():
        if name in env:
            continue
        for form in forms:
            base_dir = os.path.join(form, dirname)
            if os.path.join(base_dir, "shims") in path_entries:
                env[name] = base_dir
                break
    home = os.path.join(root, "home")
    env.update({
        "HOME": home,
        "XDG_CONFIG_HOME": os.path.join(home, ".config"),
        "XDG_STATE_HOME": os.path.join(home, ".local", "state"),
        "XDG_CACHE_HOME": os.path.join(home, ".cache"),
        "XDG_DATA_HOME": os.path.join(home, ".local", "share"),
        "GH_CONFIG_DIR": os.path.join(home, ".config", "gh"),
        "GIT_CONFIG_GLOBAL": os.path.join(home, ".gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "TMPDIR": os.path.join(root, "tmp"),
        "SHIPD_SANDBOX": "1",
        "SHIPD_SANDBOX_ROOT": root,
    })
    for name, rel in (declared.get("env") or {}).items():
        target = os.path.join(root, "state", rel)
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
        except OSError as exc:
            die(3, "cannot create %s: %s" % (os.path.dirname(target), exc))
        env[name] = target
    fake_bin = declared.get("fake_bin")
    if fake_bin:
        path = os.path.join(repo, fake_bin)
        if not os.path.isdir(path):
            die(3, "fake_bin %s does not exist" % path)
        env["PATH"] = path + os.pathsep + env.get("PATH", "")

    return subprocess.run(["bash", "-c", command], env=env).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
