#!/usr/bin/env python3
"""semdiff — a thin, mechanical structural-diff engine for the /s:review skill.

It shells out to git (and, when available, difftastic and ripgrep) and shapes
compact JSON. It makes **no** findings and assigns **no** severities — the
skill supplies the judgement. Stdlib only, no third-party imports; network
access happens only under `doctor --fix`.

Subcommands:
  diff <base> [<head>]     structural diff (syntax-aware via difft, text
                           fallback when difft is missing)
  files <base> [<head>]    changed paths grouped into architectural cohorts
  context <symbol>         best-effort reference lookup (rg, else git grep)
  change <name>            aggregate a planned shipd change's review context
  doctor [--fix]           dependency check with a tiered difft installer

Design: difftastic is *recommended*, never required — when `difft` is absent
`diff` degrades to a structural-text engine parsing `git diff` unified output
into the same JSON shape (`engine: "text"`), and never exits non-zero solely
because difftastic is missing. This mirrors the automedifftool sample but drops
its hard difft requirement and replaces its OpenSpec bridge with a shipd one.
"""

import argparse
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
# "recommended" degrades but never blocks (difft → text engine); "optional"
# has a built-in fallback or belongs to a downstream feature.
DEPS = [
    ("git", "required",
     "install git (xcode-select --install, or apt install git)."),
    ("difft", "recommended",
     "difftastic — recommended for syntax-aware diffs; its absence degrades "
     "semdiff to the text engine, it never blocks a review. Run "
     "`semdiff doctor --fix` (or: brew install difftastic)."),
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
    url = ("https://github.com/Wilfred/difftastic/releases/latest/download/"
           f"difft-{target}.tar.gz")
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
        elif tier == "recommended":
            state = ("recommended, not found — degrades to the text engine, "
                     "never blocks")
        else:
            state = "optional, not found"
        print(f"  {mark} {tool} — {state}: {hint}")
        if tier == "required":
            ok = False
    if not ok:
        print(f"{PROG}: required tools missing. Re-run with --fix to install "
              f"what can be automated (difft).", file=sys.stderr)
    return 0 if ok else 1


# --- diff -------------------------------------------------------------------


def resolve_endpoints(base, head, linear):
    """Work out what to compare.

    Returns (old_ref, new_ref, diff_spec, meta):
      - head is None → review LOCAL changes: old=base, new=None (working tree).
      - head given, PR-style (default) → old=merge-base(base, head), new=head;
        matches what GitHub shows for a PR (three-dot).
      - head given, --linear → old=base, new=head (plain two-dot A..B diff).
    new_ref is None signals "read the after side from the working tree".
    diff_spec is the ref list handed to `git diff --name-only`.
    """
    if head is None:
        return base, None, [base], {"base": base, "head": None,
                                    "mode": "working-tree"}
    if linear:
        return base, head, [base, head], {"base": base, "head": head,
                                          "mode": "linear"}
    mb = run(["git", "merge-base", base, head]).stdout.strip()
    if not mb:
        die(f"no merge base between '{base}' and '{head}' (unrelated "
            f"histories?). Use --linear for a direct comparison.")
    return mb, head, [f"{base}...{head}"], {
        "base": base, "head": head, "merge_base": mb, "mode": "merge-base",
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
    """Contents of <path> at <ref>, or empty string if it did not exist."""
    r = run(["git", "show", f"{ref}:{path}"])
    return r.stdout if r.returncode == 0 else ""


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
                hunks.append({
                    "side": "before" if side == "lhs" else "after",
                    "line": info.get("line_number"),
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
    declaration. difft line_number is 0-based; snippets are token-level, so we
    match against the full new-file line."""
    lines = new_text.splitlines()
    for h in hunks:
        if h.get("side") != "after" or h.get("line") is None:
            continue
        ln = h["line"]
        if 0 <= ln < len(lines) and any(m in lines[ln] for m in DECL_MARKERS):
            return True
    return False


def _difft_entry(old, new, path):
    """Build a diff entry for one file via difftastic.

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
    kind = "added" if not old else ("deleted" if not new else "modified")
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


def _text_entry(old, new, path, diff_spec):
    """Build a diff entry for one file by parsing `git diff` unified output.

    Returns ("ok", entry, signature_touch) or ("skip", None, False) for an
    unchanged or whitespace-only file."""
    kind = "added" if not old else ("deleted" if not new else "modified")
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
            new = ""
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, "r", errors="replace") as f:
                        new = f.read()
                except OSError:
                    continue
        else:
            new = blob_at(new_ref, path)

        action, entry, touch = ("fallback", None, False)
        if difft_available:
            action, entry, touch = _difft_entry(old, new, path)
        if action in ("fallback",) or not difft_available:
            action, entry, touch = _text_entry(old, new, path, diff_spec)
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

# Rules are segment-aware: a keyword must be a whole path segment (or a filename
# marker), so e.g. "openspec/" does NOT match the "spec" test-cohort keyword.
COHORT_RULES = [
    ("contracts", lambda p, seg, base: p.endswith(".proto") or "proto" in seg),
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


# --- context (on-demand reference lookup) -----------------------------------

# Best-effort mapping of a --lang value to a ripgrep glob.
LANG_GLOB = {
    "go": "*.go", "ts": "*.ts", "typescript": "*.ts", "tsx": "*.tsx",
    "js": "*.js", "py": "*.py", "python": "*.py", "proto": "*.proto",
    "rs": "*.rs", "rust": "*.rs", "java": "*.java", "rb": "*.rb",
}

CONTEXT_NOTE = ("best-effort candidate references; NOT a complete call graph. "
                "Unmatched files are not proven safe. Verify before trusting.")


def cmd_context(args):
    if not have("rg") and not have("git"):
        die("need ripgrep (rg) or git for lookups.", code=127)

    matches = []
    scope = args.path or "."
    if have("rg"):
        cmd = ["rg", "--json", "-w", args.symbol, scope]
        if args.lang:
            glob = LANG_GLOB.get(args.lang.lower())
            if glob:
                cmd[3:3] = ["-g", glob]
        r = run(cmd)
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
        cmd = ["git", "grep", "-n", "-w", args.symbol]
        if args.path:
            cmd += ["--", args.path]
        r = run(cmd)
        for line in r.stdout.splitlines():
            parts = line.split(":", 2)
            if len(parts) == 3:
                matches.append({"file": parts[0], "line": int(parts[1]),
                                "text": parts[2]})

    json.dump({"symbol": args.symbol, "note": CONTEXT_NOTE, "matches": matches},
              sys.stdout, indent=2)
    print()
    return 0


# --- change (planned shipd change review bridge) -------------------------------


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


def cmd_change(args):
    sc, sl = _import_engine()
    root = repo_root()
    content_dir = _content_dir(root)
    change_dir = os.path.join(root, content_dir, "planned", args.change)
    if not os.path.isdir(change_dir):
        die(f"change '{args.change}' not found under "
            f"{os.path.join(content_dir, 'planned')}/.")

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

    # Lint findings for this change, in-process.
    errors = sl.lint_change(root, args.change)
    lint = {"findings": [str(e) for e in errors]}

    json.dump({
        "change": args.change,
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

    c = sub.add_parser("context", help="on-demand reference lookup")
    c.add_argument("symbol", help="symbol to find references for")
    c.add_argument("--path", help="restrict lookup to a path")
    c.add_argument("--lang", help="restrict to a language (go/ts/py/proto/...)")
    c.set_defaults(func=cmd_context)

    ch = sub.add_parser(
        "change", help="aggregate a planned shipd change's review context")
    ch.add_argument("change", help="planned change name (under planned/)")
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
