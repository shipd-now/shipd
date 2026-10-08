#!/usr/bin/env python3
"""semdiff — a thin, mechanical structural-diff engine for the /s:review skill.

It shells out to git and difftastic (and, when available, ripgrep) and shapes
compact JSON. It makes **no** findings and assigns **no** severities — the
skill supplies the judgement. Stdlib only, no third-party imports; network
access happens only under `doctor --fix`.

Subcommands:
  diff <base> [<head>]     structural diff, syntax-aware via difft; a single
                           file whose difft output fails to parse falls back
                           to a text engine for that file alone
  files <base> [<head>]    changed paths grouped into architectural cohorts
  lint <base> [<head>]     run detected linters (ruff, flake8, pylint,
                           eslint) over changed paths only
  context <symbol>         best-effort reference lookup (rg, else git grep)
  related <base> [<head>]  bounded importer/importee context per changed
                           file (--mode balanced|max), rg/git-grep backed
  change <name>            aggregate a shipd change's review context, from
                           planned/ or the newest completed/ archive
  doctor [--fix]           dependency check with a tiered difft installer

Design: difftastic is *required* — `diff` exits non-zero when `difft` is
absent from PATH rather than degrading, because a review whose engine varies
silently produces a verdict nobody can reproduce or audit. Only a single
file's own difft parse failure still falls back to the text engine, stamping
`engine: "text"` on that file entry.
"""

import argparse
import glob
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

PROG = "semdiff"
DIFFT_VERSION = "0.71.0"


# --- shared helpers ---------------------------------------------------------


def die(msg, code=1):
    print(f"{PROG}: {msg}", file=sys.stderr)
    sys.exit(code)


def have(tool):
    return shutil.which(tool) is not None


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def in_git_repo():
    r = run(["git", "rev-parse", "--is-inside-work-tree"])
    return r.returncode == 0 and r.stdout.strip() == "true"


def repo_root():
    r = run(["git", "rev-parse", "--show-toplevel"])
    return r.stdout.strip() if r.returncode == 0 else os.getcwd()


# --- doctor (dependency provisioning) ---------------------------------------

# (tool, tier, hint). Tiers: "required" gates (exit non-zero when missing);
# "optional" has a built-in fallback or belongs to a downstream feature.
DEPS = [
    ("git", "required",
     "install git (xcode-select --install, or apt install git)."),
    ("difft", "required",
     "difftastic — required for `semdiff diff`, which exits non-zero "
     "without it. Run `semdiff doctor --fix` (or: brew install difftastic)."),
    ("rg", "optional",
     "ripgrep — optional; `semdiff context` falls back to `git grep`."),
    ("gh", "optional",
     "GitHub CLI — optional; used only by the future review gate for posting."),
]


def _difft_target():
    """Map this platform to a difftastic release target triple, or None."""
    arch = {
        "x86_64": "x86_64", "amd64": "x86_64",
        "arm64": "aarch64", "aarch64": "aarch64",
    }.get(platform.machine().lower())
    if not arch:
        return None
    system = platform.system()
    if system == "Darwin":
        return f"{arch}-apple-darwin"
    if system == "Linux":
        return f"{arch}-unknown-linux-gnu"
    return None


def _install_dir():
    """Where to drop a downloaded binary. Prefer the plugin's own bin/ (always
    on PATH while enabled); else ~/.local/bin."""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    d = os.path.join(root, "bin") if root else os.path.expanduser("~/.local/bin")
    os.makedirs(d, exist_ok=True)
    return d


def install_difft():
    """Tiered install: Homebrew, then cargo, then a prebuilt release binary.
    Network access happens here and only here — reached solely via `--fix`."""
    if have("brew"):
        print(f"{PROG}: installing difftastic via Homebrew…", file=sys.stderr)
        subprocess.run(["brew", "install", "difftastic"])
        if have("difft"):
            return True
    if have("cargo"):
        print(f"{PROG}: installing difftastic via cargo…", file=sys.stderr)
        subprocess.run(["cargo", "install", "difftastic"])
        if have("difft"):
            return True
    target = _difft_target()
    if not target:
        print(f"{PROG}: no prebuilt difft for this platform; install manually.",
              file=sys.stderr)
        return False
    url = (f"https://github.com/Wilfred/difftastic/releases/download/"
           f"{DIFFT_VERSION}/difft-{DIFFT_VERSION}-{target}.tar.gz")
    dest = _install_dir()
    print(f"{PROG}: downloading difftastic ({target}) → {dest}…",
          file=sys.stderr)
    try:
        tmp = os.path.join(tempfile.gettempdir(), "semdiff-difft.tar.gz")
        urllib.request.urlretrieve(url, tmp)  # noqa: S310 (fixed https host)
        with tarfile.open(tmp) as tf:
            member = next((m for m in tf.getmembers()
                           if os.path.basename(m.name) == "difft"), None)
            if not member:
                print(f"{PROG}: 'difft' not found inside release archive.",
                      file=sys.stderr)
                return False
            if not member.isreg():
                # The member is selected by name, so the archive decides what
                # lands on PATH: a symlink (or any other non-regular member)
                # wearing the name is refused rather than extracted.
                print(f"{PROG}: refusing to extract {member.name} from the "
                      f"release archive: it is not a regular file.",
                      file=sys.stderr)
                return False
            member.name = "difft"
            tf.extract(member, dest)
        binp = os.path.join(dest, "difft")
        os.chmod(binp, os.stat(binp).st_mode
                 | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"{PROG}: installed difft to {binp}", file=sys.stderr)
        if dest not in os.environ.get("PATH", "").split(os.pathsep):
            os.environ["PATH"] = dest + os.pathsep + os.environ.get("PATH", "")
            if not os.environ.get("CLAUDE_PLUGIN_ROOT"):
                print(f"{PROG}: NOTE — add {dest} to your shell PATH to use "
                      f"difft outside this plugin.", file=sys.stderr)
        return have("difft") or os.path.exists(binp)
    except Exception as e:  # noqa: BLE001 - report any failure and fall through
        print(f"{PROG}: prebuilt install failed: {e}", file=sys.stderr)
        return False


def cmd_doctor(args):
    ok = True
    for tool, tier, hint in DEPS:
        if have(tool):
            print(f"  + {tool}")
            continue
        if args.fix and tool == "difft" and install_difft() and have("difft"):
            print(f"  + {tool} (installed)")
            continue
        mark = "x" if tier == "required" else "-"
        if tier == "required":
            state = "MISSING (required)"
        else:
            state = "optional, not found"
        print(f"  {mark} {tool} — {state}: {hint}")
        if tier == "required":
            ok = False
    if not ok:
        print(f"{PROG}: required tools missing. Re-run with --fix to install "
              f"what can be automated (difft).", file=sys.stderr)
    base_freshness_probe(args.fix)
    return 0 if ok else 1


# --- diff -------------------------------------------------------------------


def remote_counterpart(base):
    """The commit of <base>'s remote-tracking counterpart — the branch's
    configured upstream, else `refs/remotes/origin/<base>` — or None when
    <base> is not a local branch, or carries no such counterpart.

    Read-only: no fetch, no checkout, no write of any kind. A qualified ref,
    a commit id, or a tag never matches `refs/heads/<base>`, so each is
    `None` here — the invoker's unambiguous opt-out from promotion."""
    if run(["git", "rev-parse", "--verify", "--quiet",
            f"refs/heads/{base}"]).returncode != 0:
        return None
    r = run(["git", "rev-parse", "--symbolic-full-name", f"{base}@{{upstream}}"])
    ref = r.stdout.strip() if r.returncode == 0 else f"refs/remotes/origin/{base}"
    r = run(["git", "rev-parse", "--verify", "--quiet", ref])
    return r.stdout.strip() if r.returncode == 0 else None


def _base_remote_name(base):
    """The remote a base's upstream lives on (e.g. "origin"), or "origin" as
    the same fallback `remote_counterpart` uses."""
    r = run(["git", "rev-parse", "--abbrev-ref", f"{base}@{{upstream}}"])
    return r.stdout.strip().split("/")[0] if r.returncode == 0 else "origin"


def base_freshness_probe(fix):
    """Print a report-only base-freshness line comparing the repo's default
    base branch (`main`, else `master`) against its remote-tracking
    counterpart. Without `fix` this reaches the network not at all, reading
    only already-fetched refs; with `fix` it fetches that remote first.
    Never changes `doctor`'s exit code."""
    base = None
    for candidate in ("main", "master"):
        if run(["git", "rev-parse", "--verify", "--quiet",
                f"refs/heads/{candidate}"]).returncode == 0:
            base = candidate
            break
    if base is None:
        print("  ~ base: no local main or master branch to compare")
        return
    if fix:
        run(["git", "fetch", "-q", _base_remote_name(base)])
    counterpart = remote_counterpart(base)
    if not counterpart:
        print(f"  ~ base {base}: no remote-tracking counterpart — "
              f"nothing to compare")
        return
    r = run(["git", "rev-parse", "--abbrev-ref", f"{base}@{{upstream}}"])
    ref_name = r.stdout.strip() if r.returncode == 0 else f"origin/{base}"
    counts = run(["git", "rev-list", "--left-right", "--count",
                  f"{base}...{counterpart}"]).stdout.split()
    ahead, behind = (counts + ["0", "0"])[:2]
    if ahead == "0" and behind == "0":
        print(f"  + base {base} is up to date with {ref_name}")
    else:
        print(f"  ~ base {base} is {behind} commit(s) behind {ref_name} "
              f"({ahead} ahead) — remedy: git fetch {ref_name.split('/')[0]}, "
              f"or re-run `semdiff doctor --fix`")


def resolve_endpoints(base, head, linear):
    """Work out what to compare.

    Returns (old_ref, new_ref, diff_spec, meta):
      - head is None → review LOCAL changes: old=base, new=None (working tree).
      - head given, PR-style (default) → old=merge-base(base, head), new=head;
        matches what GitHub shows for a PR (three-dot).
      - head given, --linear → old=base, new=head (plain two-dot A..B diff).
    new_ref is None signals "read the after side from the working tree".
    diff_spec is the ref list handed to `git diff --name-only`.

    <base> is promoted to its remote-tracking counterpart's commit when it
    names a short local branch carrying one — a stale local branch is never
    read as the base. A fully-qualified ref, a commit id, or a tag is taken
    as given (remote_counterpart returns None for each), which is the
    invoker's unambiguous opt-out.

    The returned meta also discloses the endpoints as commit ids:
    `base_given` (the ref as invoked, before promotion), `base_sha`,
    `head_sha` (null when the after side is the working tree), and
    `merge_base` — the fork point in working-tree mode, the three-dot merge
    base in merge-base mode, and absent under `--linear`.
    """
    base_given = base
    counterpart = remote_counterpart(base)
    if counterpart:
        base = counterpart
    if run(["git", "rev-parse", "--verify", "--quiet", base]).returncode != 0:
        die(f"unknown base ref '{base}'.")
    base_sha = run(["git", "rev-parse", base]).stdout.strip()
    head_sha = run(["git", "rev-parse", head]).stdout.strip() if head else None
    if head is None:
        fork_point = run(["git", "merge-base", base, "HEAD"]).stdout.strip()
        if not fork_point:
            die(f"no merge base between '{base}' and HEAD (unrelated "
                f"histories?).")
        return fork_point, None, [fork_point], {
            "base": base, "head": None, "mode": "working-tree",
            "base_given": base_given, "base_sha": base_sha,
            "head_sha": None, "merge_base": fork_point,
        }
    if linear:
        return base, head, [base, head], {
            "base": base, "head": head, "mode": "linear",
            "base_given": base_given, "base_sha": base_sha,
            "head_sha": head_sha,
        }
    mb = run(["git", "merge-base", base, head]).stdout.strip()
    if not mb:
        die(f"no merge base between '{base}' and '{head}' (unrelated "
            f"histories?). Use --linear for a direct comparison.")
    return mb, head, [f"{base}...{head}"], {
        "base": base, "head": head, "merge_base": mb, "mode": "merge-base",
        "base_given": base_given, "base_sha": base_sha, "head_sha": head_sha,
    }


def changed_paths(new_ref, diff_spec):
    """Files that differ across diff_spec. Untracked files are included only
    when reviewing the working tree (new_ref is None)."""
    cmd = ["git", "diff", "--name-only"] + diff_spec + ["--"]
    tracked = run(cmd)
    if tracked.returncode != 0:
        die(f"git diff failed ({' '.join(diff_spec)}): {tracked.stderr.strip()}")
    paths = [p for p in tracked.stdout.splitlines() if p]
    if new_ref is None:
        untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
        paths += [p for p in untracked.stdout.splitlines() if p]
    seen, out = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def blob_at(ref, path):
    """Contents of <path> at <ref>, or None if it did not exist there.

    The absent answer is a sentinel rather than the empty string because a
    tracked file may legitimately be empty at an endpoint: conflating the two
    reported an emptied file as `deleted` and a filled previously-empty file
    as `added`."""
    r = run(["git", "show", f"{ref}:{path}"])
    return r.stdout if r.returncode == 0 else None


# Markers that suggest a changed line declares a callable/type/message — used to
# estimate "signature changes" for the effort score (best-effort; the skill
# refines).
DECL_MARKERS = (
    "func ", "func(", "def ", "class ", "type ", "message ", "interface ",
    "fn ", "struct ", "enum ", "trait ", "service ", "rpc ",
)

# Best-effort extension → language name (the text engine has no parser; difft
# supplies real language names).
EXT_LANG = {
    ".py": "Python", ".go": "Go", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".rs": "Rust", ".java": "Java",
    ".rb": "Ruby", ".c": "C", ".h": "C", ".cc": "C++", ".cpp": "C++",
    ".sh": "Bash", ".proto": "Protocol Buffers", ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML", ".md": "Markdown", ".toml": "TOML",
    ".css": "CSS", ".scss": "SCSS", ".html": "HTML", ".sql": "SQL",
}


def _lang_for(path):
    return EXT_LANG.get(os.path.splitext(path)[1].lower())


# An added file with no hunks is otherwise reviewed on its path and line
# count alone; inlining its numbered body (capped) lets the skill judge new
# code with the same rigour it applies to a hunk, without letting a vendored
# blob swamp the review.
ADDED_CONTENT_MAX_LINES = 600
ADDED_CONTENT_MAX_BYTES = 60_000


def _inline_content(text):
    """A line-numbered rendering of `text`, each line prefixed with its
    1-based line number, capped at ADDED_CONTENT_MAX_LINES lines and
    ADDED_CONTENT_MAX_BYTES bytes.

    Returns (content, content_truncated)."""
    lines = text.splitlines()
    truncated = len(lines) > ADDED_CONTENT_MAX_LINES
    if truncated:
        lines = lines[:ADDED_CONTENT_MAX_LINES]
    numbered = []
    total_bytes = 0
    for i, line in enumerate(lines, start=1):
        entry = f"{i}: {line}"
        entry_bytes = len(entry.encode("utf-8"))
        added_bytes = entry_bytes + (1 if numbered else 0)  # "\n" join separator
        if total_bytes + added_bytes > ADDED_CONTENT_MAX_BYTES:
            truncated = True
            break
        numbered.append(entry)
        total_bytes += added_bytes
    content = "\n".join(numbered)
    return content, truncated


# -- difft engine -----------------------------------------------------------


def is_whitespace_only(chunks):
    """True if every emitted difft change is pure whitespace (formatting)."""
    saw_change = False
    for chunk in chunks:
        for line in chunk:
            for side in ("lhs", "rhs"):
                for ch in (line.get(side) or {}).get("changes", []):
                    saw_change = True
                    if ch.get("content", "").strip() != "":
                        return False
    return saw_change


def summarize_chunks(chunks):
    """Compact per-line summary: which side/line changed and a joined snippet."""
    hunks = []
    for chunk in chunks:
        for line in chunk:
            for side in ("lhs", "rhs"):
                info = line.get(side) or {}
                changes = info.get("changes", [])
                if not changes:
                    continue
                snippet = "".join(c.get("content", "") for c in changes)
                line_number = info.get("line_number")
                hunks.append({
                    "side": "before" if side == "lhs" else "after",
                    # difftastic reports a 0-based line_number; normalize to
                    # 1-based so both engines agree with `grep -n` truth.
                    "line": line_number + 1 if line_number is not None else None,
                    "snippet": snippet,
                })
    return hunks


def difft_json(old_text, new_text, name):
    """Run difftastic on a temp pair, return its parsed JSON object (or None)."""
    env = dict(os.environ, DFT_UNSTABLE="yes")
    with tempfile.TemporaryDirectory() as d:
        base, ext = os.path.splitext(os.path.basename(name))
        old_p = os.path.join(d, f"{base}.old{ext}")
        new_p = os.path.join(d, f"{base}.new{ext}")
        with open(old_p, "w") as f:
            f.write(old_text)
        with open(new_p, "w") as f:
            f.write(new_text)
        r = run(["difft", "--display", "json", old_p, new_p], env=env)
        if r.returncode not in (0, 1) or not r.stdout.strip():
            return None
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return None


def _touches_declaration_difft(new_text, hunks):
    """True if any 'after' difft hunk lands on a line that looks like a
    declaration. Hunk `line` is 1-based (normalized in summarize_chunks);
    snippets are token-level, so we match against the full new-file line."""
    lines = new_text.splitlines()
    for h in hunks:
        if h.get("side") != "after" or h.get("line") is None:
            continue
        ln = h["line"]
        if 1 <= ln <= len(lines) and any(m in lines[ln - 1] for m in DECL_MARKERS):
            return True
    return False


def _difft_entry(old, new, path, kind):
    """Build a diff entry for one file via difftastic.

    `old`/`new` are the endpoint texts (empty where the file is absent there),
    `kind` the classification the caller derived from presence.

    Returns ("ok", entry, signature_touch) on success, ("skip", None, False)
    for an unchanged/whitespace-only file, or ("fallback", None, False) when
    difft output could not be used (the caller retries with the text engine)."""
    obj = difft_json(old, new, path)
    if obj is None:
        return "fallback", None, False
    status = obj.get("status")
    if status == "unchanged":
        return "skip", None, False
    chunks = obj.get("chunks", [])
    # Drop pure-formatting noise only for genuine content edits. Whole-file
    # adds/deletes carry no chunks but MUST still surface.
    if status == "changed" and is_whitespace_only(chunks):
        return "skip", None, False
    hunks = summarize_chunks(chunks)
    entry = {
        "path": path,
        "language": obj.get("language") or _lang_for(path),
        "kind": kind,
        "hunks": hunks,
        "engine": "difft",
    }
    if kind in ("added", "deleted") and not hunks:
        entry["lines"] = (new if kind == "added" else old).count("\n") + 1
        if kind == "added":
            entry["content"], entry["content_truncated"] = _inline_content(new)
    touch = kind != "deleted" and _touches_declaration_difft(new, hunks)
    return "ok", entry, touch


# -- text engine ------------------------------------------------------------

HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _parse_unified_hunks(patch):
    """Parse a unified `git diff` patch body into difft-shaped hunk entries.

    Line numbers are 1-based (git's own numbering). File headers, index lines,
    and the `+++`/`---` markers are skipped."""
    hunks = []
    old_ln = new_ln = 0
    for line in patch.splitlines():
        m = HUNK_HEADER_RE.match(line)
        if m:
            new_ln = int(m.group(1))
            # old start is in the -a,b group; recompute cheaply.
            om = re.match(r"^@@ -(\d+)", line)
            old_ln = int(om.group(1)) if om else 0
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            hunks.append({"side": "after", "line": new_ln,
                          "snippet": line[1:]})
            new_ln += 1
        elif line.startswith("-"):
            hunks.append({"side": "before", "line": old_ln,
                          "snippet": line[1:]})
            old_ln += 1
        elif line.startswith(" "):
            old_ln += 1
            new_ln += 1
        # `\ No newline at end of file` and other lines are ignored.
    return hunks


def _has_content_change(diff_spec, path, ignore_ws):
    """True if `git diff` for one path shows any added/removed content line.
    With ignore_ws, whitespace-only differences are ignored (`git diff -w`)."""
    cmd = ["git", "diff"]
    if ignore_ws:
        cmd.append("-w")
    cmd += diff_spec + ["--", path]
    patch = run(cmd).stdout
    for line in patch.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line and line[0] in "+-":
            return True
    return False


def _text_entry(old, new, path, diff_spec, kind):
    """Build a diff entry for one file by parsing `git diff` unified output.

    `old`/`new` are the endpoint texts (empty where the file is absent there),
    `kind` the classification the caller derived from presence.

    Returns ("ok", entry, signature_touch) or ("skip", None, False) for an
    unchanged or whitespace-only file."""
    entry = {
        "path": path,
        "language": _lang_for(path),
        "kind": kind,
        "hunks": [],
        "engine": "text",
    }
    if kind in ("added", "deleted"):
        # Whole-file add/delete: no per-line hunks; carry a size so the skill
        # can decide whether to read the file itself.
        entry["lines"] = (new if kind == "added" else old).count("\n") + 1
        if kind == "added":
            entry["content"], entry["content_truncated"] = _inline_content(new)
        touch = False
        return "ok", entry, touch
    # Modified: filter whitespace-only edits, then parse real hunks.
    if not _has_content_change(diff_spec, path, ignore_ws=True):
        return "skip", None, False
    patch = run(["git", "diff"] + diff_spec + ["--", path]).stdout
    hunks = _parse_unified_hunks(patch)
    entry["hunks"] = hunks
    touch = any(h["side"] == "after"
                and any(m in h["snippet"] for m in DECL_MARKERS)
                for h in hunks)
    return "ok", entry, touch


def cmd_diff(args):
    if not have("git"):
        die("required tool 'git' not found on PATH. install git.", code=127)
    if not in_git_repo():
        die("not inside a git repository.")
    if not have("difft"):
        die("required tool 'difft' not found on PATH. install difftastic "
            "(run `semdiff doctor --fix`, or: brew install difftastic).",
            code=127)

    old_ref, new_ref, diff_spec, meta = resolve_endpoints(
        args.base, args.head, args.linear)
    root = repo_root()
    difft_available = have("difft")
    results = []
    signature_changes = 0

    for path in changed_paths(new_ref, diff_spec):
        old = blob_at(old_ref, path)
        if new_ref is None:
            abs_path = os.path.join(root, path)
            new = None
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, "r", errors="replace") as f:
                        new = f.read()
                except OSError:
                    continue
        else:
            new = blob_at(new_ref, path)

        # Presence at each endpoint, not emptiness there, is what the kind
        # says: an emptied file is still present, and so is a file that was
        # empty before it was filled. Both are modifications.
        kind = ("added" if old is None
                else "deleted" if new is None else "modified")
        old, new = old or "", new or ""

        action, entry, touch = ("fallback", None, False)
        if difft_available:
            action, entry, touch = _difft_entry(old, new, path, kind)
        if action in ("fallback",) or not difft_available:
            action, entry, touch = _text_entry(old, new, path, diff_spec, kind)
        if action == "skip":
            continue
        results.append(entry)
        if touch:
            signature_changes += 1

    kinds = {"added": 0, "deleted": 0, "modified": 0}
    for r in results:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    engine = ("difft" if difft_available and results
              and all(r["engine"] == "difft" for r in results) else "text")
    summary = {
        "files": len(results),
        "languages": sorted({r["language"] for r in results
                             if r.get("language")}),
        "hunks": sum(len(r["hunks"]) for r in results),
        "kinds": kinds,
        "signature_changes": signature_changes,
        "engine": engine,
    }
    json.dump({**meta, "summary": summary, "files": results},
              sys.stdout, indent=2)
    print()
    return 0


# --- files (cohort grouping) ------------------------------------------------

# A packaging or dependency manifest declares what the package ships, exports
# and depends on — a contract, and reviewed as one. Matched on the basename, so
# a manifest anywhere in the tree lands in `contracts` rather than inheriting
# the cohort of whatever directory holds it.
MANIFEST_BASENAMES = frozenset((
    "package.json", "package-lock.json", "npm-shrinkwrap.json",
    "yarn.lock", "pnpm-lock.yaml",
    "go.mod", "go.sum", "go.work", "go.work.sum",
    "cargo.toml", "cargo.lock",
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
    "pipfile", "pipfile.lock", "poetry.lock", "uv.lock",
    "gemfile", "gemfile.lock", "podfile", "podfile.lock",
    "composer.json", "composer.lock",
    "pom.xml", "build.gradle", "build.gradle.kts", "build.sbt",
    "directory.packages.props", "directory.build.props",
    "packages.config", "packages.lock.json",
    "package.swift", "package.resolved",
    "mix.exs", "mix.lock",
    "pubspec.yaml", "pubspec.lock",
))

# Manifests whose basename varies by project or package, so no exact-name set
# can hold them — a C# project file is named after its project, a gemspec
# after its gem.
MANIFEST_SUFFIXES = (".csproj", ".fsproj", ".vbproj", ".gemspec", ".nuspec",
                     ".cabal")


def _is_manifest(base):
    """True when ``base`` names a packaging or dependency manifest.

    Three shapes, because manifests do not share one naming convention:
    an exact name (`package.json`), a project-specific suffix
    (`Acme.Api.csproj`), and the `requirements*.txt` family, whose split
    files (`requirements-dev.txt`) are as much a declaration as the plain
    one.
    """
    low = base.lower()
    return (low in MANIFEST_BASENAMES
            or low.endswith(MANIFEST_SUFFIXES)
            or (low.startswith("requirements") and low.endswith(".txt")))

# Rules are segment-aware: a keyword must be a whole path segment (or a filename
# marker), so e.g. "openspec/" does NOT match the "spec" test-cohort keyword.
COHORT_RULES = [
    ("contracts", lambda p, seg, base: p.endswith(".proto") or "proto" in seg
     or _is_manifest(base)),
    ("database", lambda p, seg, base: {"models", "model", "repository",
     "store", "db", "migrations"} & seg or "migration" in base
     or "schema" in base),
    ("api", lambda p, seg, base: {"api", "routes", "route", "endpoints",
     "controllers", "handlers"} & seg or "handler" in base
     or "controller" in base),
    ("frontend", lambda p, seg, base: p.endswith((".tsx", ".jsx", ".vue",
     ".css", ".scss")) or {"components", "frontend", "web", "ui"} & seg),
    ("tests", lambda p, seg, base: {"tests", "test", "spec", "specs"} & seg
     or any(m in base for m in ("_test.", ".test.", ".spec.", "_spec."))),
]


def _build_scripts_dir():
    """Absolute path to the build skill's scripts/ (the cross-skill engine
    import point — the established convention)."""
    return os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "build", "scripts"))


def _content_dir(root):
    """The repo's content-directory name (default `.shipd`), resolved through
    the engine's layered configuration. Falls back to `.shipd` if the engine
    cannot be imported."""
    try:
        build = _build_scripts_dir()
        if build not in sys.path:
            sys.path.insert(0, build)
        import spec_common as sc  # noqa: WPS433 (local import by design)
        config, _prov = sc.resolve_config(root)
        return sc.specs_dirname(config)
    except Exception:  # noqa: BLE001 - config is best-effort for cohorting
        return ".shipd"


def cohort_of(path, content_dir):
    """Classify a path into an architectural cohort. shipd-aware groups —
    plugin skills and content-dir spec artifacts — take precedence so this
    repo's own changes group sensibly; then the segment-aware generic rules;
    then the top-level directory."""
    parts = path.split("/")
    seg = set(parts[:-1])  # directory segments only
    base = os.path.basename(path)
    top = parts[0] if len(parts) > 1 else None
    if top == "plugins" and "skills" in seg:
        return "skills"
    if top == content_dir:
        return "specs"
    for name, rule in COHORT_RULES:
        if rule(path, seg, base):
            return name
    return top if "/" in path else "root"


def cmd_files(args):
    if not have("git"):
        die("required tool 'git' not found on PATH. install git.", code=127)
    if not in_git_repo():
        die("not inside a git repository.")
    _, new_ref, diff_spec, meta = resolve_endpoints(
        args.base, args.head, args.linear)
    content_dir = _content_dir(repo_root())
    groups = {}
    for path in changed_paths(new_ref, diff_spec):
        groups.setdefault(cohort_of(path, content_dir), []).append(path)
    ordered = {k: sorted(v) for k, v in sorted(groups.items())}
    summary = {"files": sum(len(v) for v in ordered.values()),
               "cohorts": len(ordered)}
    json.dump({**meta, "summary": summary, "cohorts": ordered},
              sys.stdout, indent=2)
    print()
    return 0


# --- lint (static analysis subcommand) --------------------------------------

# Findings a linter run may report, in the shape every subcommand emits
# (review-lint-subcommand): {"path", "line", "rule", "message", "severity"}.

DEFAULT_LINT_TIMEOUT = 30.0

# JavaScript/TypeScript extensions eslint owns.
JS_TS_EXTENSIONS = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts",
                    ".cts")

_INI_SECTION_RE_CACHE = {}


def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def _has_marker_file(root, *names):
    return any(os.path.isfile(os.path.join(root, n)) for n in names)


def _has_glob_marker(root, *patterns):
    return any(glob.glob(os.path.join(root, pat)) for pat in patterns)


def _has_ini_section(root, filename, section):
    """True if `filename` (INI or TOML — both use `[section]` headers)
    carries a `[section]` header on its own line."""
    text = _read_text(os.path.join(root, filename))
    if text is None:
        return False
    pattern = _INI_SECTION_RE_CACHE.get(section)
    if pattern is None:
        pattern = re.compile(r"(?m)^\s*\[" + re.escape(section) + r"\]\s*$")
        _INI_SECTION_RE_CACHE[section] = pattern
    return bool(pattern.search(text))


def _detect_ruff(root):
    return (_has_marker_file(root, "ruff.toml", ".ruff.toml")
            or _has_ini_section(root, "pyproject.toml", "tool.ruff"))


def _detect_flake8(root):
    return (_has_marker_file(root, ".flake8")
            or _has_ini_section(root, "setup.cfg", "flake8")
            or _has_ini_section(root, "tox.ini", "flake8"))


def _detect_pylint(root):
    return (_has_marker_file(root, ".pylintrc")
            or _has_ini_section(root, "pyproject.toml", "tool.pylint"))


def _detect_eslint(root):
    return _has_glob_marker(root, "eslint.config.*", ".eslintrc*")


def _finding(path, line, rule, message, severity):
    return {"path": path, "line": line, "rule": rule, "message": message,
            "severity": severity}


def _parse_ruff_output(text):
    data = json.loads(text or "[]")
    findings = []
    for item in data:
        loc = item.get("location") or {}
        findings.append(_finding(
            item.get("filename", ""), loc.get("row"), item.get("code") or "",
            item.get("message", ""), "warning"))
    return findings


def _parse_flake8_output(text):
    data = json.loads(text or "{}")
    findings = []
    for path, violations in data.items():
        for v in violations:
            findings.append(_finding(
                path, v.get("line_number"), v.get("code", ""),
                v.get("text", ""), "warning"))
    return findings


def _parse_pylint_output(text):
    data = json.loads(text or "[]")
    findings = []
    for item in data:
        findings.append(_finding(
            item.get("path", ""), item.get("line"),
            item.get("symbol") or item.get("message-id") or "",
            item.get("message", ""), item.get("type") or "warning"))
    return findings


def _parse_eslint_output(text):
    data = json.loads(text or "[]")
    findings = []
    for file_result in data:
        path = file_result.get("filePath", "")
        for msg in file_result.get("messages", []):
            severity = "error" if msg.get("severity") == 2 else "warning"
            findings.append(_finding(
                path, msg.get("line"), msg.get("ruleId") or "",
                msg.get("message", ""), severity))
    return findings


# The detection table (review-lint-subcommand): each of the four linters maps
# to its detector, its resolvable binary name, the file extensions it owns in
# a diff, the argv fragment requesting its machine-readable format, and its
# output parser. Order matches plan.md's table (ruff, flake8, pylint, eslint).
LINTERS = {
    "ruff": {
        "detect": _detect_ruff,
        "binary": "ruff",
        "extensions": (".py",),
        "format_argv": ["--output-format", "json"],
        "parse": _parse_ruff_output,
    },
    "flake8": {
        "detect": _detect_flake8,
        "binary": "flake8",
        "extensions": (".py",),
        "format_argv": ["--format=json"],
        "parse": _parse_flake8_output,
    },
    "pylint": {
        "detect": _detect_pylint,
        "binary": "pylint",
        "extensions": (".py",),
        "format_argv": ["--output-format=json"],
        "parse": _parse_pylint_output,
    },
    "eslint": {
        "detect": _detect_eslint,
        "binary": "eslint",
        "extensions": JS_TS_EXTENSIONS,
        "format_argv": ["--format", "json"],
        "parse": _parse_eslint_output,
    },
}

STDERR_EXCERPT_MAX = 4000


def _truncate(text):
    text = text or ""
    if len(text) > STDERR_EXCERPT_MAX:
        return text[:STDERR_EXCERPT_MAX] + "…"
    return text


def _resolve_binary(root, name):
    """Resolve `name`'s executable, preferring the repository's own
    `node_modules/.bin` over `PATH` (review-lint-subcommand: "the project's
    own install wins")."""
    local = os.path.join(root, "node_modules", ".bin", name)
    if os.path.isfile(local) and os.access(local, os.X_OK):
        return local
    return shutil.which(name)


def _lint_config(root):
    """The resolved `lint` configuration (shipd-config `lint` key), read
    through the same `spec_common.resolve_config` path `_content_dir` uses.
    Falls back to the defaults — no scripts run, nothing disabled — when the
    engine cannot be imported or the layer is malformed."""
    lint_cfg = {}
    try:
        build = _build_scripts_dir()
        if build not in sys.path:
            sys.path.insert(0, build)
        import spec_common as sc  # noqa: WPS433 (local import by design)
        config, _prov = sc.resolve_config(root)
        raw = config.get("lint")
        if isinstance(raw, dict):
            lint_cfg = raw
    except Exception:  # noqa: BLE001 - lint config resolution degrades safely
        lint_cfg = {}
    run_scripts = bool(lint_cfg.get("run_scripts", False))
    raw_disable = lint_cfg.get("disable")
    disable = set(raw_disable) if isinstance(raw_disable, list) else set()
    return {"run_scripts": run_scripts, "disable": disable}


def _partition_paths(paths, extensions):
    return [p for p in paths if os.path.splitext(p)[1].lower() in extensions]


def _npm_lint_script_declared(root):
    data_text = _read_text(os.path.join(root, "package.json"))
    if data_text is None:
        return False
    try:
        data = json.loads(data_text)
    except ValueError:
        return False
    if not isinstance(data, dict):
        return False
    scripts = data.get("scripts")
    return isinstance(scripts, dict) and isinstance(scripts.get("lint"), str)


def _execute_linter(argv, timeout, parse):
    """Run one linter's `argv` under `timeout` and parse its stdout.

    Returns (state, findings, stderr_excerpt_or_None). A non-zero exit is
    normal (findings exist); only a timeout, an execution failure, or output
    that does not parse sets `failed` (review-lint-subcommand)."""
    try:
        r = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return "failed", [], _truncate(
            f"linter exceeded its {timeout}s timeout")
    except OSError as e:
        return "failed", [], _truncate(f"failed to execute linter: {e}")
    try:
        findings = parse(r.stdout)
    except Exception as e:  # noqa: BLE001 - any parse failure degrades safely
        excerpt = (r.stderr or "").strip() or f"could not parse output: {e}"
        return "failed", [], _truncate(excerpt)
    return "ran", findings, None


def _execute_script(argv, timeout):
    """Run a repository-defined script under `timeout`. No structured
    findings are parsed from arbitrary script output — only its execution
    outcome is reported."""
    try:
        subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "failed", _truncate(f"script exceeded its {timeout}s timeout")
    except OSError as e:
        return "failed", _truncate(f"failed to execute script: {e}")
    return "ran", None


def cmd_lint(args):
    if not have("git"):
        die("required tool 'git' not found on PATH. install git.", code=127)
    if not in_git_repo():
        die("not inside a git repository.")

    _, new_ref, diff_spec, meta = resolve_endpoints(
        args.base, args.head, args.linear)
    root = repo_root()
    paths = changed_paths(new_ref, diff_spec)
    lint_cfg = _lint_config(root)
    disabled = lint_cfg["disable"]
    timeout = args.timeout

    entries = []
    counts = {"ran": 0, "unavailable": 0, "skipped": 0, "not-run": 0,
              "failed": 0}
    total_findings = 0

    for name, spec in LINTERS.items():
        if name in disabled:
            if not spec["detect"](root):
                continue
            entry = {"name": name, "state": "skipped", "argv": [],
                     "findings": []}
        elif not spec["detect"](root):
            continue
        else:
            binary = _resolve_binary(root, spec["binary"])
            if binary is None:
                entry = {"name": name, "state": "unavailable", "argv": [],
                         "findings": []}
            else:
                owned = _partition_paths(paths, spec["extensions"])
                if not owned:
                    entry = {"name": name, "state": "skipped", "argv": [],
                             "findings": []}
                else:
                    argv = [binary] + spec["format_argv"] + owned
                    state, findings, stderr = _execute_linter(
                        argv, timeout, spec["parse"])
                    entry = {"name": name, "state": state, "argv": argv,
                             "findings": findings}
                    if stderr is not None:
                        entry["stderr"] = stderr
        entries.append(entry)
        counts[entry["state"]] += 1
        total_findings += len(entry["findings"])

    if _npm_lint_script_declared(root) and "npm-lint-script" not in disabled:
        if not lint_cfg["run_scripts"]:
            entry = {"name": "npm-lint-script", "state": "not-run",
                     "argv": [], "findings": []}
        else:
            npm_bin = _resolve_binary(root, "npm")
            if npm_bin is None:
                entry = {"name": "npm-lint-script", "state": "unavailable",
                         "argv": [], "findings": []}
            else:
                argv = [npm_bin, "run", "lint"]
                state, stderr = _execute_script(argv, timeout)
                entry = {"name": "npm-lint-script", "state": state,
                         "argv": argv, "findings": []}
                if stderr is not None:
                    entry["stderr"] = stderr
        entries.append(entry)
        counts[entry["state"]] += 1

    summary = {"findings": total_findings, **counts}
    json.dump({**meta, "linters": entries, "summary": summary},
              sys.stdout, indent=2)
    print()
    return 0


# --- context (on-demand reference lookup) -----------------------------------

# Best-effort mapping of a --lang value to a ripgrep glob.
LANG_GLOB = {
    "go": "*.go", "ts": "*.ts", "typescript": "*.ts", "tsx": "*.tsx",
    "js": "*.js", "py": "*.py", "python": "*.py", "proto": "*.proto",
    "rs": "*.rs", "rust": "*.rs", "java": "*.java", "rb": "*.rb",
}

CONTEXT_NOTE = ("best-effort candidate references; NOT a complete call graph. "
                "Unmatched files are not proven safe. Verify before trusting.")


class GrepFailure(RuntimeError):
    """Raised by `_grep_matches` when the underlying `rg`/`git grep`
    subprocess exits with a status that is neither "matched" (0) nor the
    tool's own documented "no matches" exit (1) — a real tool failure
    (a bad pattern, a filesystem error, `git` refusing to run), which must
    never be read as "no related files". Silently treating this the same as
    an empty result would let a review proceed believing a search ran and
    found nothing, when in fact the search never ran at all."""


def _grep_matches(pattern, path=None, word=True, lang=None, fixed=False):
    """Best-effort search for `pattern` across the repo (or `path`), via
    ripgrep when present and `git grep` otherwise — the one tool ladder both
    `context` and `related` run. `word` requests a whole-word match; `fixed`
    requests a literal (non-regex) match, for a term such as a path that may
    carry regex metacharacters. Returns a list of {"file", "line", "text"}
    dicts. Raises `GrepFailure` when the subprocess itself failed (see
    `GrepFailure`) rather than returning an empty list indistinguishable from
    a genuine no-match result."""
    matches = []
    scope = path or "."
    if have("rg"):
        cmd = ["rg", "--json"]
        if word:
            cmd.append("-w")
        if fixed:
            cmd.append("-F")
        if lang:
            glob = LANG_GLOB.get(lang.lower())
            if glob:
                cmd += ["-g", glob]
        cmd += [pattern, scope]
        r = run(cmd)
        if r.returncode not in (0, 1):
            raise GrepFailure(
                "rg exited %d: %s" % (r.returncode, (r.stderr or "").strip()))
        for line in r.stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "match":
                continue
            data = ev["data"]
            matches.append({
                "file": data["path"]["text"],
                "line": data["line_number"],
                "text": data["lines"]["text"].rstrip("\n"),
            })
    else:
        cmd = ["git", "grep", "-n"]
        if word:
            cmd.append("-w")
        if fixed:
            cmd.append("-F")
        cmd.append(pattern)
        if path:
            cmd += ["--", path]
        r = run(cmd)
        if r.returncode not in (0, 1):
            raise GrepFailure(
                "git grep exited %d: %s"
                % (r.returncode, (r.stderr or "").strip()))
        for line in r.stdout.splitlines():
            parts = line.split(":", 2)
            if len(parts) == 3:
                matches.append({"file": parts[0], "line": int(parts[1]),
                                "text": parts[2]})
    return matches


def cmd_context(args):
    if not have("rg") and not have("git"):
        die("need ripgrep (rg) or git for lookups.", code=127)

    try:
        matches = _grep_matches(args.symbol, path=args.path, lang=args.lang)
    except GrepFailure as exc:
        die("search failed: %s" % exc)

    json.dump({"symbol": args.symbol, "note": CONTEXT_NOTE, "matches": matches},
              sys.stdout, indent=2)
    print()
    return 0


# --- related (bounded importer/importee context) ----------------------------

# balanced is the default: a per-file cap of 8 and a per-review cap of 40.
# max raises both for a review where recall matters more than cost. These
# numbers are deliberate and recorded in the spec (related-context) rather
# than left as an unstated tuning knob, so a later change can move them
# against evidence rather than by feel.
RELATED_CAPS = {
    "balanced": {"per_file": 8, "per_review": 40},
    "max": {"per_file": 20, "per_review": 120},
}

# Source extensions `related` tries when resolving an extensionless import
# token to a file on disk.
IMPORT_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
                     ".go", ".rs", ".rb", ".java", ".proto", ".h", ".hpp",
                     ".c", ".cc", ".cpp")

# Lines that name another module: Python import/from, JS/TS import-from and
# require(), Rust use, and C/C++ #include. Each pattern's one capture group is
# the raw module/path token(s) (comma-separated for Python's `import a, b`).
_IMPORT_LINE_PATTERNS = (
    re.compile(r'^\s*from\s+([.\w]+)\s+import\b'),
    re.compile(r'^\s*import\s+([.\w]+(?:\s*,\s*[.\w]+)*)'),
    re.compile(r'''\bfrom\s+['"]([^'"]+)['"]'''),
    re.compile(r'''^\s*import\s+['"]([^'"]+)['"]'''),
    re.compile(r'''\brequire\(\s*['"]([^'"]+)['"]\s*\)'''),
    re.compile(r'^\s*use\s+([\w:]+)'),
    re.compile(r'^\s*#\s*include\s+["<]([^">]+)[">]'),
)

# Go's grouped import form, `import (\n\t"path"\n\t...\n)`, names each path
# on its own line with no keyword beside it — none of the per-line patterns
# above can match it, since they all require a keyword on the same line as
# the quoted path. Matched separately, across the whole text.
_GO_IMPORT_BLOCK_RE = re.compile(r'(?m)^\s*import\s*\((.*?)^\s*\)', re.DOTALL)
_GO_IMPORT_PATH_RE = re.compile(r'"([^"]+)"')


def _module_terms(path):
    """The search terms for `path`'s importers: its basename without
    extension (what an import statement typically names), plus its own
    extensionless repo path for languages that import by path, when that
    differs from the bare basename."""
    base = os.path.splitext(os.path.basename(path))[0]
    extensionless = os.path.splitext(path)[0]
    terms = [base]
    if extensionless != base:
        terms.append(extensionless)
    return terms


def _find_importers(changed_file, root):
    """Files that *import* `changed_file` — matched by import syntax, never
    by a bare occurrence of its name. Grep finds candidate files mentioning
    `changed_file`'s module terms (cheap, best-effort, and restricted to
    source files before this even runs); each candidate's own full text is
    then parsed for import/require/use/include lines the same way an
    importee is — never just the single grep-matched line, because a
    grouped import (Go's parenthesized block; a multi-line JS/TS or Python
    import) puts the keyword and the quoted path on different lines — and
    the candidate is kept only when one of its extracted tokens resolves to
    `changed_file` itself. A documentation or spec file that merely
    discusses the module in prose never parses as import syntax, so it is
    never reported as an importer."""
    found = set()
    checked = set()
    for term in _module_terms(changed_file):
        if not term:
            continue
        for m in _grep_matches(term, word=True, fixed=True):
            candidate = m["file"]
            if candidate == changed_file or candidate in checked:
                continue
            checked.add(candidate)
            if os.path.splitext(candidate)[1].lower() not in IMPORT_EXTENSIONS:
                continue
            text = _file_text_at(None, candidate, root)
            for token in _importee_tokens(text):
                if _resolve_importee(token, candidate, root) == changed_file:
                    found.add(candidate)
                    break
    return found


def _importee_tokens(text):
    """Raw module/path tokens named by `text`'s own import/require/use/
    include lines, plus any Go grouped-import block."""
    tokens = []
    for line in text.splitlines():
        for pat in _IMPORT_LINE_PATTERNS:
            m = pat.search(line)
            if not m:
                continue
            for piece in m.group(1).split(","):
                piece = re.sub(r'\s+as\s+\w+\s*$', "", piece.strip())
                if piece:
                    tokens.append(piece)
    for block in _GO_IMPORT_BLOCK_RE.findall(text):
        tokens.extend(_GO_IMPORT_PATH_RE.findall(block))
    return tokens


def _exists_with_extension(rel_path, root):
    """`rel_path`, or `rel_path` plus a common source extension or index
    file, resolved against `root` — the first that names a real file inside
    `root`. Returns the matching repo-relative path (forward slashes), or
    None.

    A token with enough `../` segments (or a leading-dot Python import
    climbing past the package root) can normalize to a path outside `root`
    entirely. `os.path.isfile` alone does not care — it happily stats
    whatever the join produces, repo or not — so every candidate's real path
    is checked against `root`'s real path before it is accepted. Without
    this, a crafted or merely deep relative import in the diff could make
    `related` name, and the review then read, a file outside the repository
    (per the `related-context` spec: "An importee SHALL resolve to a path
    that exists in the repository" — in the repository, not merely on disk)."""
    rel_path = os.path.normpath(rel_path)
    if rel_path in (".", "", ".."):
        return None
    if os.path.splitext(rel_path)[1]:
        candidates = [rel_path]
    else:
        candidates = [rel_path + ext for ext in IMPORT_EXTENSIONS] + [
            os.path.join(rel_path, "__init__.py"),
            os.path.join(rel_path, "index.ts"),
            os.path.join(rel_path, "index.js"),
            os.path.join(rel_path, "mod.rs"),
        ]
    root_real = os.path.realpath(root)
    for cand in candidates:
        abs_path = os.path.join(root, cand)
        if not os.path.isfile(abs_path):
            continue
        real = os.path.realpath(abs_path)
        if real != root_real and not real.startswith(root_real + os.sep):
            continue  # escapes root — never named, same as "resolves to nothing"
        return cand.replace(os.sep, "/")
    return None


def _find_unique_source_file(basename, root):
    """Last-resort fallback for a bare import name that resolves neither
    relative to the importing file nor to the repo root — the
    cross-skill-import convention this repo's own scripts use, which adds a
    sibling `scripts/` directory to `sys.path` at runtime rather than
    importing by a path the text alone names. A single file named
    `basename.<ext>`, for a recognized source extension, anywhere in the
    repository is accepted; more than one is ambiguous and dropped rather
    than guessed at, the same as a name that resolves to nothing at all."""
    matches = set()
    for ext in IMPORT_EXTENSIONS:
        for hit in glob.glob(
                os.path.join(root, "**", basename + ext), recursive=True):
            matches.add(os.path.relpath(hit, root).replace(os.sep, "/"))
    return next(iter(matches)) if len(matches) == 1 else None


def _resolve_importee(token, changed_file, root):
    """Resolve one import token named by `changed_file` to an existing
    repo-relative path, or None when it names nothing in the repository —
    dropped rather than guessed at, per the spec."""
    token = token.strip()
    if not token:
        return None
    file_dir = os.path.dirname(changed_file)

    if token.startswith("../") or token.startswith("./"):
        # JS/TS/Go/C-style relative path: resolved directly against the
        # importing file's own directory. Checked before the bare-dot
        # Python branch below, because a token here always carries a "/"
        # right after its leading dots — and `os.path.join` treats a
        # component starting with "/" as an absolute path, silently
        # discarding everything before it, so routing this shape through
        # the dots-as-package-levels math corrupts the join instead of
        # resolving it.
        return _exists_with_extension(os.path.join(file_dir, token), root)

    if token.startswith("."):
        # Python-style relative import: leading dots count package levels up.
        dots = len(token) - len(token.lstrip("."))
        rest = token[dots:].replace(".", "/")
        base_dir = file_dir
        for _ in range(dots - 1):
            base_dir = os.path.dirname(base_dir)
        joined = os.path.join(base_dir, rest) if rest else base_dir
        return _exists_with_extension(joined, root)

    if "/" in token:
        return (_exists_with_extension(token, root)
                or _exists_with_extension(os.path.join(file_dir, token), root))

    dotted = token.replace(".", "/") if "." in token else token
    resolved = (_exists_with_extension(os.path.join(file_dir, dotted), root)
                or _exists_with_extension(dotted, root))
    if resolved or "/" in dotted:
        return resolved
    return _find_unique_source_file(dotted, root)


def _find_importees(changed_file, text, root):
    """Files `changed_file` itself imports, resolved against the repo and
    deduplicated, in first-seen order."""
    found, seen = [], set()
    for token in _importee_tokens(text):
        resolved = _resolve_importee(token, changed_file, root)
        if resolved and resolved != changed_file and resolved not in seen:
            seen.add(resolved)
            found.append(resolved)
    return found


def _file_text_at(new_ref, path, root):
    """Contents of `path` on the after side: the working tree when reviewing
    local changes (`new_ref` is None), else the blob at `new_ref`."""
    if new_ref is None:
        abs_path = os.path.join(root, path)
        if not os.path.isfile(abs_path):
            return ""
        try:
            with open(abs_path, "r", errors="replace") as fh:
                return fh.read()
        except OSError:
            return ""
    return blob_at(new_ref, path) or ""


def _proximity_key(changed_file, candidate):
    """Sort key ranking `candidate` by proximity to `changed_file`: same
    directory first, then by the depth of their nearest common ancestor
    (deeper shared prefix sorts earlier), so the per-file cap keeps the files
    most likely to matter."""
    cdirs = changed_file.split("/")[:-1]
    kdirs = candidate.split("/")[:-1]
    if cdirs == kdirs:
        return (0, 0, candidate)
    common = 0
    for a, b in zip(cdirs, kdirs):
        if a != b:
            break
        common += 1
    return (1, -common, candidate)


def cmd_related(args):
    if not have("rg") and not have("git"):
        die("need ripgrep (rg) or git for lookups.", code=127)
    if not in_git_repo():
        die("not inside a git repository.")

    caps = RELATED_CAPS[args.mode]
    per_file_cap, per_review_cap = caps["per_file"], caps["per_review"]

    # Resolve the changed-file list the same way `files` does, so the two
    # subcommands never disagree about what changed.
    _, new_ref, diff_spec, _meta = resolve_endpoints(
        args.base, args.head, args.linear)
    changed = changed_paths(new_ref, diff_spec)
    root = repo_root()

    # Phase 1: collect every changed file's full ranked candidate list, with
    # no budget applied. The per-file cap bounds what is *listed*, not what
    # is collected — the allocator below needs each file's total candidate
    # count (for scarce-first ordering across files) and its truncation
    # count has to reflect everything dropped, whether by the per-file cap
    # or by the per-review budget.
    tags = {}
    ranked = {}
    for path in changed:
        # Only a recognized source file has a module name worth searching
        # for, or import/require/use/include lines worth scanning. A
        # changed doc/spec/manifest file's basename is as likely to be an
        # ordinary word ("plan", "tasks", "spec") as a module name — running
        # the same search against one would return every unrelated file that
        # happens to use that word, which is noise, not related context.
        if os.path.splitext(path)[1].lower() in IMPORT_EXTENSIONS:
            try:
                importer_files = _find_importers(path, root)
            except GrepFailure as exc:
                # A failed search is not "no importers" — reporting it as an
                # empty result would have the review proceed believing the
                # diff carries no cross-file context when the search for it
                # never actually ran. Fail the whole subcommand loudly,
                # the same way "neither rg nor git" already does, so the
                # review records this among what it could not verify rather
                # than silently trusting an empty set.
                die("search failed while resolving importers for %s: %s"
                    % (path, exc))
            text = _file_text_at(new_ref, path, root)
            importee_files = _find_importees(path, text, root)
        else:
            importer_files, importee_files = set(), []

        tag = {}
        for f in importer_files:
            tag[f] = "importer"
        for f in importee_files:
            tag.setdefault(f, "importee")
        tags[path] = tag

        # Importees rank above importers — what a changed file calls is more
        # directly relevant than an arbitrary sample of its callers — each
        # group ordered by the existing proximity key, unchanged.
        importees = sorted((f for f in tag if tag[f] == "importee"),
                            key=lambda f: _proximity_key(path, f))
        importers = sorted((f for f in tag if tag[f] == "importer"),
                            key=lambda f: _proximity_key(path, f))
        ranked[path] = importees + importers

    # Phase 2: allocate the per-review budget in fair-share passes. On each
    # pass, every changed file with an unallocated candidate takes its next
    # one, subject to the per-file cap, so no changed file receives a second
    # related file while another candidate-bearing file has none. Within a
    # pass, files are visited in ascending order of total candidate count
    # (ties broken by path, for a deterministic allocation), so a file with
    # few candidates is served before a hub with many. A related file
    # already selected for another changed file costs nothing further —
    # charged against the per-review cap once — so passes keep running past
    # budget exhaustion as long as some file's next candidate is already
    # selected, and stop only once no file has an unallocated candidate it
    # can afford, free or otherwise.
    kept = {path: [] for path in changed}
    cursor = {path: 0 for path in changed}
    selected = set()
    remaining = per_review_cap
    order = sorted(changed, key=lambda f: (len(ranked[f]), f))

    progress = True
    while progress:
        progress = False
        for path in order:
            if cursor[path] >= len(ranked[path]):
                continue
            if len(kept[path]) >= per_file_cap:
                continue
            candidate = ranked[path][cursor[path]]
            free = candidate in selected
            if not free and remaining <= 0:
                continue
            cursor[path] += 1
            kept[path].append(candidate)
            if not free:
                selected.add(candidate)
                remaining -= 1
            progress = True

    entries = {}
    total_truncated = 0
    files_without_candidates = 0
    files_starved = 0
    for path in changed:
        tag = tags[path]
        kept_files = kept[path]
        file_truncated = len(ranked[path]) - len(kept_files)
        total_truncated += file_truncated

        entries[path] = {
            "importers": sorted(f for f in kept_files if tag[f] == "importer"),
            "importees": sorted(f for f in kept_files if tag[f] == "importee"),
            "truncated": file_truncated,
        }

        if not ranked[path]:
            files_without_candidates += 1
        elif not kept_files:
            files_starved += 1

    related_edges = sum(
        len(e["importers"]) + len(e["importees"]) for e in entries.values())

    json.dump({
        "mode": args.mode,
        "note": CONTEXT_NOTE,
        "caps": {"per_file": per_file_cap, "per_review": per_review_cap},
        "files": entries,
        "summary": {
            "changed_files": len(changed),
            "related_files": len(selected),
            "related_edges": related_edges,
            "truncated": total_truncated,
            "files_without_candidates": files_without_candidates,
            "files_starved": files_starved,
        },
    }, sys.stdout, indent=2)
    print()
    return 0


# --- change (shipd change review bridge, planned or archived) -----------------


def _import_engine():
    """Import the build skill's spec engine in-process (the established
    cross-skill convention). Returns (spec_common, spec_lint)."""
    build = _build_scripts_dir()
    if build not in sys.path:
        sys.path.insert(0, build)
    import spec_common as sc  # noqa: WPS433
    import spec_lint as sl  # noqa: WPS433
    return sc, sl


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


STATUS_RE = re.compile(r"^Status:\s*(.*?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^\s*- \[([ ~x])\]\s*(.*?)\s*$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
_SLASH_PATH_RE = re.compile(r"^[\w\-./]+$")
_DOTTED_FILE_RE = re.compile(r"^[\w\-.]+\.[A-Za-z][A-Za-z0-9]{0,7}$")


def _is_path_like(tok):
    """Best-effort: a backtick token that reads like a file path — either it
    contains a directory separator or it is a dotted filename with an
    alphabetic extension. Bare identifiers (e.g. `auth`) are excluded."""
    if not tok or " " in tok:
        return False
    if "/" in tok:
        return bool(_SLASH_PATH_RE.match(tok))
    return bool(_DOTTED_FILE_RE.match(tok))


def _impact_files(plan_text):
    seen, out = set(), []
    for tok in BACKTICK_RE.findall(plan_text):
        tok = tok.strip()
        if _is_path_like(tok) and tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def _req_delta(operation, capability, req):
    return {
        "operation": operation,
        "capability": capability,
        "requirement_id": req.id,
        "requirement_title": req.title,
        "requirement_text": req.body,
        "scenarios": [s.text for s in req.scenarios],
    }


def _resolve_change_dir(root, content_dir, change):
    """Resolve a change directory for reading: ``planned/<change>/`` first and,
    when absent, the archived ``completed/*-<change>/`` — the lexicographically
    last (newest date prefix) when several match, mirroring the status CLI's
    `cat change`. Returns ``(location, absolute_dir)``, or ``(None, None)``
    when the change lives under neither directory."""
    planned = os.path.join(root, content_dir, "planned", change)
    if os.path.isdir(planned):
        return "planned", planned
    archives = sorted(
        path for path in glob.glob(
            os.path.join(root, content_dir, "completed", "*-" + change))
        if os.path.isdir(path))
    if archives:
        return "completed", archives[-1]
    return None, None


def cmd_change(args):
    sc, sl = _import_engine()
    root = repo_root()
    content_dir = _content_dir(root)
    location, change_dir = _resolve_change_dir(root, content_dir, args.change)
    if location is None:
        die(f"change '{args.change}' not found under "
            f"{os.path.join(content_dir, 'planned')}/ or "
            f"{os.path.join(content_dir, 'completed')}/.")
    rel_dir = os.path.relpath(change_dir, root)

    plan_path = os.path.join(change_dir, "plan.md")
    plan_text = _read(plan_path) if os.path.isfile(plan_path) else ""
    status_m = STATUS_RE.search(plan_text)
    status = status_m.group(1) if status_m else None

    # Deltas per capability.
    deltas = []
    specs_root = os.path.join(change_dir, "specs")
    if os.path.isdir(specs_root):
        for capability in sorted(os.listdir(specs_root)):
            spec_path = os.path.join(specs_root, capability, "spec.md")
            if not os.path.isfile(spec_path):
                continue
            delta = sc.parse_delta(_read(spec_path))
            for req in delta.added:
                deltas.append(_req_delta("added", capability, req))
            for req in delta.modified:
                deltas.append(_req_delta("modified", capability, req))
            for req in delta.removed:
                deltas.append(_req_delta("removed", capability, req))
            for ren in delta.renamed:
                deltas.append({"operation": "renamed", "capability": capability,
                               "from": ren.from_id, "to": ren.to_id})

    # Tasks: checkbox states and progress.
    tasks_path = os.path.join(change_dir, "tasks.md")
    items = []
    if os.path.isfile(tasks_path):
        for line in _read(tasks_path).splitlines():
            m = CHECKBOX_RE.match(line)
            if m:
                items.append({"checked": m.group(1) == "x",
                              "state": m.group(1),
                              "text": m.group(2)})
    done = sum(1 for it in items if it["checked"])
    tasks = {"total": len(items), "done": done, "items": items}

    # Lint findings for this change, in-process. The linter runs over planned/
    # only, so an archive reports why it was skipped instead.
    if location == "planned":
        errors = sl.lint_change(root, args.change)
        lint = {"findings": [str(e) for e in errors]}
    else:
        lint = {"findings": [],
                "skipped": "archived change: its deltas are already merged "
                           "into verified/ and the linter runs over planned/ "
                           "only"}

    json.dump({
        "change": args.change,
        "location": location,
        "dir": rel_dir,
        "status": status,
        "deltas": deltas,
        "tasks": tasks,
        "lint": lint,
        "impact_files": _impact_files(plan_text),
    }, sys.stdout, indent=2)
    print()
    return 0


# --- cli --------------------------------------------------------------------


def _add_endpoint_args(sub, with_head=True):
    sub.add_argument("base", help="base git ref (e.g. main)")
    if with_head:
        sub.add_argument(
            "head", nargs="?", default=None,
            help="optional head ref; omit to review the working tree. With a "
                 "head, defaults to PR-style merge-base (three-dot) semantics.")
        sub.add_argument(
            "--linear", action="store_true",
            help="with a head ref, use a plain two-dot base..head diff "
                 "instead of merge-base")


def main():
    p = argparse.ArgumentParser(prog=PROG, description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser(
        "diff", help="structural diff of a base ref vs working tree or a head")
    _add_endpoint_args(d)
    d.set_defaults(func=cmd_diff)

    f = sub.add_parser("files", help="changed files grouped by cohort")
    _add_endpoint_args(f)
    f.set_defaults(func=cmd_files)

    lt = sub.add_parser(
        "lint", help="run detected static-analysis linters over changed "
                     "paths only")
    _add_endpoint_args(lt)
    lt.add_argument(
        "--timeout", type=float, default=DEFAULT_LINT_TIMEOUT,
        help="per-linter timeout in seconds (default: "
             f"{DEFAULT_LINT_TIMEOUT})")
    lt.set_defaults(func=cmd_lint)

    c = sub.add_parser("context", help="on-demand reference lookup")
    c.add_argument("symbol", help="symbol to find references for")
    c.add_argument("--path", help="restrict lookup to a path")
    c.add_argument("--lang", help="restrict to a language (go/ts/py/proto/...)")
    c.set_defaults(func=cmd_context)

    rel = sub.add_parser(
        "related",
        help="bounded, per-changed-file importer/importee context")
    _add_endpoint_args(rel)
    rel.add_argument(
        "--mode", choices=sorted(RELATED_CAPS), default="balanced",
        help="balanced (default): 8 related files per changed file, 40 "
             "per review. max: 20 per changed file, 120 per review.")
    rel.set_defaults(func=cmd_related)

    ch = sub.add_parser(
        "change",
        help="aggregate a shipd change's review context, resolved under "
             "planned/ or completed/")
    ch.add_argument(
        "change",
        help="change name; resolved under planned/, else the newest "
             "completed/<date>-<name>/ archive")
    ch.set_defaults(func=cmd_change)

    doc = sub.add_parser(
        "doctor", help="check (and optionally install) review tools")
    doc.add_argument("--fix", action="store_true",
                     help="install missing tools that can be automated (difft)")
    doc.set_defaults(func=cmd_doctor)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
