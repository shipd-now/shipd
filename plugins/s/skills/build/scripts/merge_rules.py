#!/usr/bin/env python3
"""merge_rules.py — the engine behind ``shipd gate rules``
(shipd-cli gate-rules-verb): map the ``merge`` configuration onto the one
GitHub ruleset shipd owns, report how the live ruleset differs, and create or
update it.

Stdlib-only (plus ``spec_common`` for the configuration). Every GitHub call
goes through one injectable runner ``run(args, stdin=None, cwd=None)`` that
returns ``(returncode, stdout, stderr)``, so tests drive the whole module with
a recording fake and never reach the network. The module only ever lists the
repository's rulesets, reads the detail of the one named :data:`RULESET_NAME`,
and writes that one — never any other ruleset.

The drift pieces (:func:`find_owned`, :func:`live_members`, :func:`diff`) are
public so a later doctor check can reuse them unchanged.
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import spec_common  # noqa: E402

# The one ruleset shipd owns; any other ruleset is never fetched or written.
RULESET_NAME = "shipd merge rules"

# Seconds a single ``gh`` call may take before it reports as a failure.
GH_TIMEOUT = 30

# The six ``merge`` members in report order, then the ruleset-level members the
# diff also checks.
MERGE_MEMBERS = ("approvals", "dismiss_stale", "last_push_approval",
                 "required_checks", "thread_resolution", "strict")
EXTRA_MEMBERS = ("enforcement", "target", "ref_include",
                 "bypass_actors")

_DEFAULT_REF = "~DEFAULT_BRANCH"


class RulesError(Exception):
    """A failure the verb reports as ``Error: <message>`` and exit ``1``."""


def gh_run(args, stdin=None, cwd=None):
    """``(returncode, stdout, stderr)`` for ``gh <args...>``, bounded by
    :data:`GH_TIMEOUT`; a timeout or a missing ``gh`` reports as an ordinary
    failure."""
    try:
        proc = subprocess.run(["gh"] + list(args), input=stdin, cwd=cwd,
                              capture_output=True, text=True,
                              timeout=GH_TIMEOUT)
    except subprocess.TimeoutExpired:
        return (1, "", "gh timed out after %ds" % GH_TIMEOUT)
    except OSError as exc:
        return (1, "", str(exc))
    return (proc.returncode, proc.stdout, proc.stderr)


def _wanted_checks(merge):
    return list(merge["required_checks"])


def desired_ruleset(merge):
    """The ruleset body ``merge`` asks for (the shape observed on a live
    ruleset: read-only response fields are not sent). The
    ``required_status_checks`` rule is omitted when no check is required."""
    rules = [{
        "type": "pull_request",
        "parameters": {
            "required_approving_review_count": merge["approvals"],
            "dismiss_stale_reviews_on_push": merge["dismiss_stale"],
            "require_code_owner_review": False,
            "require_last_push_approval": merge["last_push_approval"],
            "required_review_thread_resolution": merge["thread_resolution"],
        },
    }]
    checks = _wanted_checks(merge)
    if checks:
        rules.append({
            "type": "required_status_checks",
            "parameters": {
                "required_status_checks": [{"context": c} for c in checks],
                "strict_required_status_checks_policy": merge["strict"],
            },
        })
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": [_DEFAULT_REF],
                                    "exclude": []}},
        "bypass_actors": [],
        "rules": rules,
    }


def _rule_params(detail, kind):
    for rule in detail.get("rules") or []:
        if isinstance(rule, dict) and rule.get("type") == kind:
            params = rule.get("parameters")
            return params if isinstance(params, dict) else {}
    return None


def live_members(detail):
    """The six ``merge`` members read back out of a ruleset ``detail``. A rule
    the ruleset lacks reads as the loosest value (0 approvals, false flags, no
    checks)."""
    pr = _rule_params(detail, "pull_request") or {}
    sc_params = _rule_params(detail, "required_status_checks") or {}
    checks = sorted(
        c.get("context") for c in sc_params.get("required_status_checks") or []
        if isinstance(c, dict) and c.get("context"))
    return {
        "approvals": pr.get("required_approving_review_count", 0),
        "dismiss_stale": bool(pr.get("dismiss_stale_reviews_on_push", False)),
        "last_push_approval": bool(pr.get("require_last_push_approval",
                                          False)),
        "required_checks": checks,
        "thread_resolution": bool(pr.get("required_review_thread_resolution",
                                         False)),
        "strict": bool(sc_params.get("strict_required_status_checks_policy",
                                     False)),
    }


def _live_ref_include(detail):
    ref = ((detail.get("conditions") or {}).get("ref_name") or {})
    return sorted(ref.get("include") or [])


def compare(merge, detail):
    """Every checked member as ``(member, live, wanted)`` in fixed order —
    the six ``merge`` members, then ``enforcement``, ``target``, and
    ``ref_include``, and ``bypass_actors`` (a count, wanted 0) — whether or not they differ. ``required_checks`` compare
    as sorted lists, and ``strict`` is wanted false when no check is required
    (the rule carrying it is then omitted)."""
    live = live_members(detail)
    wanted = {
        "approvals": merge["approvals"],
        "dismiss_stale": merge["dismiss_stale"],
        "last_push_approval": merge["last_push_approval"],
        "required_checks": sorted(_wanted_checks(merge)),
        "thread_resolution": merge["thread_resolution"],
        "strict": bool(merge["strict"] and merge["required_checks"]),
    }
    rows = [(m, live[m], wanted[m]) for m in MERGE_MEMBERS]
    rows.append(("enforcement", detail.get("enforcement"), "active"))
    rows.append(("target", detail.get("target"), "branch"))
    rows.append(("ref_include", _live_ref_include(detail), [_DEFAULT_REF]))
    rows.append(("bypass_actors", len(detail.get("bypass_actors") or []), 0))
    return rows


def diff(merge, detail):
    """The members of ``detail`` that differ from ``merge``, as
    ``(member, live, wanted)`` in fixed member order."""
    return [(m, live, want) for m, live, want in compare(merge, detail)
            if live != want]


def _failure(what, err):
    err = (err or "").strip()
    if "403" in err:
        return RulesError(
            "%s failed: GitHub refused (403) — managing rulesets needs "
            "repository admin permission (%s)" % (what, err))
    return RulesError("%s failed: %s" % (what, err or "unknown error"))


def _api_json(run, args, what, stdin=None, cwd=None):
    code, out, err = run(args, stdin=stdin, cwd=cwd)
    if code != 0:
        raise _failure(what, err)
    try:
        return json.loads(out) if out.strip() else {}
    except ValueError:
        raise RulesError("%s returned a body that is not JSON" % what)


def find_owned(nwo, run, cwd=None):
    """The list entry of the repository's one ruleset named
    :data:`RULESET_NAME`, or ``None`` when there is none. Only
    repository-sourced rulesets count. Raises :class:`RulesError` on more than
    one match or a failed call. Other rulesets are never fetched."""
    items = _api_json(
        run, ["api", "repos/%s/rulesets?includes_parents=false&per_page=100"
              % nwo], "listing rulesets", cwd=cwd)
    owned = [i for i in items if isinstance(i, dict)
             and i.get("name") == RULESET_NAME
             and i.get("source_type") == "Repository"]
    if len(owned) > 1:
        raise RulesError(
            "%d rulesets in %s are named `%s` (ids %s); remove the extras "
            "so one remains" % (len(owned), nwo, RULESET_NAME,
                                ", ".join(str(i.get("id")) for i in owned)))
    return owned[0] if owned else None


def _get_detail(nwo, rid, run, cwd=None):
    return _api_json(run, ["api", "repos/%s/rulesets/%s" % (nwo, rid)],
                     "reading ruleset %s" % rid, cwd=cwd)


def _fmt(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[%s]" % ", ".join(str(v) for v in value)
    return str(value)


def show(nwo, merge, run, out, cwd=None):
    """Print the configured merge rules beside the live ruleset, one line per
    member marked ``ok`` or ``differs``. Writes nothing."""
    item = find_owned(nwo, run, cwd=cwd)
    if item is None:
        out("merge rules for %s: no ruleset named `%s` exists yet "
            "(`shipd gate rules apply` creates it)" % (nwo, RULESET_NAME))
        for member in MERGE_MEMBERS:
            want = compare(merge, {})[MERGE_MEMBERS.index(member)][2]
            out("%s: config %s, live (none) (differs)" % (member, _fmt(want)))
        return 0
    detail = _get_detail(nwo, item["id"], run, cwd=cwd)
    out("merge rules for %s: ruleset `%s` (id %s)"
        % (nwo, RULESET_NAME, item["id"]))
    for member, live, want in compare(merge, detail):
        out("%s: config %s, live %s (%s)" % (
            member, _fmt(want), _fmt(live),
            "ok" if live == want else "differs"))
    return 0


def apply(nwo, merge, run, out, cwd=None):
    """Create the ruleset when absent, update it in place when present and
    different, and write nothing when it already matches."""
    body = json.dumps(desired_ruleset(merge))
    item = find_owned(nwo, run, cwd=cwd)
    if item is None:
        result = _api_json(
            run, ["api", "-X", "POST", "repos/%s/rulesets" % nwo,
                  "--input", "-"], "creating the ruleset", stdin=body, cwd=cwd)
        out("created ruleset `%s` (id %s)" % (RULESET_NAME, result.get("id")))
        for member, _live, want in compare(merge, {}):
            out("%s: (none) -> %s" % (member, _fmt(want)))
        return 0
    detail = _get_detail(nwo, item["id"], run, cwd=cwd)
    changes = diff(merge, detail)
    if not changes:
        out("ruleset `%s` (id %s) already matches the merge configuration; "
            "nothing written" % (RULESET_NAME, item["id"]))
        return 0
    _api_json(run, ["api", "-X", "PUT",
                    "repos/%s/rulesets/%s" % (nwo, item["id"]),
                    "--input", "-"], "updating the ruleset", stdin=body,
              cwd=cwd)
    out("updated ruleset `%s` (id %s)" % (RULESET_NAME, item["id"]))
    for member, live, want in changes:
        out("%s: %s -> %s" % (member, _fmt(live), _fmt(want)))
    return 0


def _resolve_repo(repo, root, run):
    if repo:
        return repo
    code, out, err = run(["repo", "view", "--json", "nameWithOwner", "-q",
                          ".nameWithOwner"], cwd=root)
    if code != 0 or not out.strip():
        raise RulesError("cannot resolve the repository from %s: %s — pass "
                         "--repo OWNER/NAME" % (root, (err or "").strip()
                                                or "no output"))
    return out.strip()


def main(argv, run=gh_run, out=print):
    """Run ``shipd gate rules [apply] [--repo OWNER/NAME] [--root DIR]`` (the
    arguments after ``rules``) and return the exit code."""
    parser = argparse.ArgumentParser(
        prog="shipd gate rules",
        description="Report, or with `apply` write, the one GitHub ruleset "
                    "named `%s`, from the `merge` configuration. Bare, it "
                    "changes nothing." % RULESET_NAME)
    parser.add_argument("action", nargs="?", choices=["apply"],
                        help="apply: create or update the ruleset "
                             "(default: report only)")
    parser.add_argument("--repo", help="OWNER/NAME (default: the repository "
                                       "`gh repo view` resolves from --root)")
    parser.add_argument("--root", default=os.getcwd(),
                        help="repository root (default: cwd)")
    opts = parser.parse_args(argv)
    root = os.path.abspath(opts.root)
    try:
        merge = spec_common.resolve_merge(root)
        nwo = _resolve_repo(opts.repo, root, run)
        if opts.action == "apply":
            return apply(nwo, merge, run, out, cwd=root)
        return show(nwo, merge, run, out, cwd=root)
    except (spec_common.ConfigError, RulesError) as exc:
        sys.stderr.write("Error: %s\n" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
