#!/usr/bin/env python3
"""Port automikk's tree into the shipd namespace.

Verbs:
  plan    Report the operations a port would perform; writes nothing.
  apply   Perform the port.
  verify  Scan an existing destination for residual matches.

Exit codes: 0 clean, 2 findings reported, 1 a general error (printed as
`Error: <message>` on stderr).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


class PortError(Exception):
    """A general port-tool error: reported as `Error: <message>`, exit 1."""


def _run_git(args, cwd=None, binary=False):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=not binary,
        )
    except FileNotFoundError as exc:
        raise PortError(f"git not found: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        message = stderr.strip() if stderr else str(exc)
        raise PortError(message) from exc
    return result.stdout


def _check_source_is_git_repo(source):
    _run_git(["-C", source, "rev-parse", "--is-inside-work-tree"])


def _list_source_files(source, ref):
    """Return the paths tracked at `ref`, as reported by `git ls-files`."""
    output = _run_git(["-C", source, "ls-files", f"--with-tree={ref}"])
    return [line for line in output.splitlines() if line]


def _read_source_file(source, ref, path):
    """Return the bytes of `path` as committed at `ref`."""
    return _run_git(["-C", source, "show", f"{ref}:{path}"], binary=True)


# Trees the epic drops entirely: never read, never written.
_EXCLUDED_PREFIXES = ("openspec/", ".automikk/")


def _select_source_paths(source, ref, includes=None):
    """Return the tracked paths at `ref`, minus the excluded trees.

    When `includes` is given (a list of prefixes), only paths starting with
    one of them are returned; otherwise the whole non-excluded tree is
    returned.
    """
    paths = [
        path
        for path in _list_source_files(source, ref)
        if not path.startswith(_EXCLUDED_PREFIXES)
    ]
    if includes:
        paths = [
            path for path in paths if any(path.startswith(p) for p in includes)
        ]
    return paths


_CAPABILITY_VERIFIED_PREFIX = ".am/verified/"
_CAPABILITY_SLUG_RE = re.compile(r"^am-[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*$")


def _enumerate_capability_slugs(source, ref):
    """Return the `am-<name>` capability slugs enumerated under `.am/verified/`.

    Directories are taken literally from the tracked file paths, never
    guessed by a general `am-<word>` pattern over text.
    """
    slugs = set()
    for path in _list_source_files(source, ref):
        if not path.startswith(_CAPABILITY_VERIFIED_PREFIX):
            continue
        rest = path[len(_CAPABILITY_VERIFIED_PREFIX):]
        slug = rest.split("/", 1)[0]
        if _CAPABILITY_SLUG_RE.match(slug):
            slugs.add(slug)
    return sorted(slugs)


def _capability_rename_rules(source, ref):
    """Build word-bounded `am-<name>` -> `shipd-<name>` substitution rules."""
    slugs = sorted(_enumerate_capability_slugs(source, ref), key=len, reverse=True)
    rules = []
    for slug in slugs:
        name = slug[len("am-"):]
        pattern = re.compile(r"\b" + re.escape(slug) + r"\b")
        rules.append((pattern, f"shipd-{name}"))
    return rules


# The ordered, longest-and-most-specific-first token rules, exactly as
# enumerated in plan.md's `## Implementation` (rules 1-13). Capability slugs
# (rule 10) and the quoted content-directory segment rule (rule 11) are
# spliced in at their positions by `build_rules`, below. No rule here ever
# matches a bare `am`.
_STATIC_RULES_HEAD = [
    ("am@automikk", "s@shipd"),  # 1
    (".am-config.json", ".shipd-config.json"),  # 2
    ("AM_WORKTREE_IDLE_MINUTES", "SHIPD_WORKTREE_IDLE_MINUTES"),  # 3
    ("~/.am-memory", "~/.shipd-memory"),  # 4
    ("~/.am/builds", "~/.shipd/builds"),  # 5
    (".cache/automikk", ".cache/shipd"),  # 6
    ("plugins/am/", "plugins/s/"),  # 7
    ("am:oracle", "s:oracle"),  # 8
    ("am:sub-agent", "s:sub-agent"),  # 8
    ("am:validator", "s:validator"),  # 8
    ("/am:", "/s:"),  # 9
]

_STATIC_RULES_TAIL = [
    (".am/", ".shipd/"),  # 12
    ("automikk", "shipd"),  # 13
    ("Automikk", "Shipd"),  # 13
]

# 11. A complete quoted `.am` segment -> the same-quoted `.shipd`. Matches
# only when the quoted string is exactly `.am`, never a longer string like
# `.am-config.json` or `.among`.
_QUOTED_SEGMENT_RULE = (
    re.compile(r"""(["'])\.am\1"""),
    lambda match: f"{match.group(1)}.shipd{match.group(1)}",
)


def _literal_rule(literal, replacement):
    return (re.compile(re.escape(literal)), replacement)


def build_rules(source, ref):
    """Build the ordered token substitution rule list for a source ref.

    Each rule is a `(compiled pattern, replacement)` pair. Rules are applied
    in order, to both file content and paths.
    """
    rules = [_literal_rule(old, new) for old, new in _STATIC_RULES_HEAD]
    rules.extend(_capability_rename_rules(source, ref))
    rules.append(_QUOTED_SEGMENT_RULE)
    rules.extend(_literal_rule(old, new) for old, new in _STATIC_RULES_TAIL)
    return rules


def apply_rules(text, rules):
    """Apply an ordered list of `(pattern, replacement)` rules to `text`."""
    for pattern, replacement in rules:
        text = pattern.sub(replacement, text)
    return text


# Residual-scan detector: matches a whole token (a run of non-whitespace)
# containing either the bare word `automikk` (any case) or an "anchored"
# `am` shape structurally like the ones the token map above rewrites —
# `.am-...`/`.am/...`, `/am-.../am:.../am/...`, `am:`/`am@`, or an
# `AM_..._`-style constant — but never a bare `am` and never a general
# `am-<word>` capability slug (those are legitimately left alone when not
# enumerated; see the `port-capability-enum` requirement).
_RESIDUAL_RE = re.compile(
    r"""
    \S*[Aa]utomikk\S*
    | \S*\.am(?=[-/])\S*
    | \S*/am(?=[-/:])\S*
    | \S*\bam(?=[:@])\S*
    | \bAM_[A-Z0-9_]+\b
    """,
    re.VERBOSE,
)


def _scan_text(rel_path, text):
    """Return `(rel_path, line_number, match)` residual findings in `text`."""
    findings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in _RESIDUAL_RE.finditer(line):
            findings.append((rel_path, line_no, match.group(0)))
    return findings


def _report_findings(findings):
    """Print each finding as `<path>:<line>: <match>`; return the exit code."""
    for rel_path, line_no, match in findings:
        print(f"{rel_path}:{line_no}: {match}")
    return 2 if findings else 0


def cmd_plan(args):
    _check_source_is_git_repo(args.source)
    rules = build_rules(args.source, args.ref)
    paths = _select_source_paths(args.source, args.ref, args.include)
    for path in paths:
        dest_rel = apply_rules(path, rules)
        print(f"PORT {path} -> {dest_rel}")
    return 0


def cmd_apply(args):
    _check_source_is_git_repo(args.source)
    rules = build_rules(args.source, args.ref)
    paths = _select_source_paths(args.source, args.ref, args.include)
    dest_root = Path(args.dest)
    findings = []
    for path in paths:
        content = _read_source_file(args.source, args.ref, path)
        dest_rel = apply_rules(path, rules)
        dest_path = dest_root / dest_rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            # Binary/non-UTF-8: copied byte-for-byte, never substituted,
            # and excluded from the residual scan.
            dest_path.write_bytes(content)
            continue
        ported_text = apply_rules(text, rules)
        dest_path.write_text(ported_text)
        findings.extend(_scan_text(dest_rel, ported_text))
    return _report_findings(findings)


def cmd_verify(args):
    dest_root = Path(args.dest)
    findings = []
    for file_path in sorted(dest_root.rglob("*")):
        if not file_path.is_file():
            continue
        rel_path = file_path.relative_to(dest_root)
        if rel_path.parts and rel_path.parts[0] == ".git":
            continue
        try:
            text = file_path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            # Binary/non-UTF-8: excluded from the residual scan.
            continue
        findings.extend(_scan_text(str(rel_path), text))
    return _report_findings(findings)


def build_parser():
    parser = argparse.ArgumentParser(prog="port.py")
    subparsers = parser.add_subparsers(dest="verb", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--source", required=True)
    plan_parser.add_argument("--ref", default="HEAD")
    plan_parser.add_argument("--dest", required=True)
    plan_parser.add_argument("--include", action="append", default=None)
    plan_parser.set_defaults(func=cmd_plan)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--source", required=True)
    apply_parser.add_argument("--ref", default="HEAD")
    apply_parser.add_argument("--dest", required=True)
    apply_parser.add_argument("--include", action="append", default=None)
    apply_parser.set_defaults(func=cmd_apply)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--dest", required=True)
    verify_parser.set_defaults(func=cmd_verify)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PortError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
