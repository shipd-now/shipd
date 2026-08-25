#!/usr/bin/env python3
"""guardrails.py — the PreToolUse guardrail hook (stdlib only, no network, no
third-party imports).

Claude Code invokes this script before every ``Edit`` and ``Write`` tool call,
handing it the hook payload as JSON on stdin. The script extracts the lines the
call would *add*, matches them against the resolved rule registry, and — when a
rule fires — prints a PreToolUse ``deny`` decision whose reason carries the
violated rule's corrective message. The model reads that reason and retries
differently, so the unwanted line never reaches the file.

Three built-in rules ship active in every repository (change-log comments,
step-narration comments, placeholder comments); ``.shipd-config.json``'s
``guardrails`` key disables the hook, drops individual rules, or adds its own.

**The hook fails open, always.** Unparseable stdin, malformed config, an
uncompilable pattern, or any unexpected exception exits 0 without denying: this
runs on every edit in every repository, so an erroring hook would break all
editing. ``SHIPD_GUARDRAILS=off`` in the environment bypasses it entirely.
"""

import fnmatch
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

DEFAULT_RULES = [
    {
        "name": "changelog-comment",
        "pattern": r"(?i)(?:#|//)\s*(?:added|updated|changed|fixed|new|"
                   r"refactored)\s*:",
        "message": "Change-log comments narrate the edit rather than the code. "
                   "Drop the comment, or replace it with a constraint the code "
                   "itself cannot show.",
    },
    {
        "name": "narrating-comment",
        "pattern": r"(?i)(?:#|//)\s*(?:now|then|next|first|finally),?\s+"
                   r"(?:we|i|it)\s",
        "message": "Step-narration comments restate the line below them. "
                   "Delete the comment and let the code speak.",
    },
    {
        "name": "filler-placeholder",
        "pattern": r"(?i)(?:#|//)\s*(?:\.\.\.\s*)?(?:rest of |existing code|"
                   r"remains? unchanged|unchanged below|no changes? "
                   r"(?:here|needed))",
        "message": "Placeholder comments stand in for content that must be "
                   "written. Write the full content instead of eliding it.",
    },
]


def added_lines(tool_name, tool_input):
    """Return the lines the call would add (guardrail-added-line-matching).

    ``Edit``: the ``new_string`` lines that are not present, as exact line
    matches, among the ``old_string`` lines — so a line merely moved or kept is
    never re-flagged. ``Write``: every line of ``content``. Any other tool
    contributes nothing.
    """
    if tool_name == "Edit":
        old = set(str(tool_input.get("old_string") or "").splitlines())
        new = str(tool_input.get("new_string") or "").splitlines()
        return [line for line in new if line not in old]
    if tool_name == "Write":
        return str(tool_input.get("content") or "").splitlines()
    return []


def declared_guardrails(start):
    """Return the ``guardrails`` value resolved for ``start``, or ``None``.

    Resolution is the standard layered per-key merge (shipd-config
    layered-key-merge): the nearest ``.shipd-config.json`` declaring the key
    wins it wholesale. A missing key, an unreadable layer, or a malformed
    config file all read as undeclared — this hook never errors on config.
    """
    try:
        import spec_common
        config, _ = spec_common.resolve_config(start)
        return config.get("guardrails")
    except Exception:
        return None


def valid_rule(rule):
    """Whether a config-declared rule carries the required string members."""
    if not isinstance(rule, dict):
        return False
    return all(isinstance(rule.get(key), str) and rule.get(key)
               for key in ("name", "pattern", "message"))


def resolve_rules(start):
    """Return the rule registry governing ``start``, or ``None`` when the hook
    is turned off there (shipd-config guardrails-key).

    Start from the built-ins in order; a config rule repeating a ``name``
    replaces that rule in place, the rest append; then every name in
    ``disable`` is dropped. A malformed ``guardrails`` value is treated as
    undeclared, and an individual malformed rule is skipped.
    """
    declared = declared_guardrails(start)
    if declared is False:
        return None
    rules = list(DEFAULT_RULES)
    if not isinstance(declared, dict):
        return rules
    declared_rules = declared.get("rules")
    for rule in declared_rules if isinstance(declared_rules, list) else []:
        if not valid_rule(rule):
            continue
        for index, existing in enumerate(rules):
            if existing["name"] == rule["name"]:
                rules[index] = rule
                break
        else:
            rules.append(rule)
    disable = declared.get("disable")
    if isinstance(disable, list):
        dropped = {name for name in disable if isinstance(name, str)}
        rules = [rule for rule in rules if rule["name"] not in dropped]
    return rules


def rule_applies(rule, file_path):
    """Whether ``rule``'s optional ``files`` globs accept ``file_path``."""
    globs = rule.get("files")
    if not globs:
        return True
    if not isinstance(globs, list):
        return False
    path = str(file_path or "")
    return any(isinstance(pattern, str) and fnmatch.fnmatch(path, pattern)
               for pattern in globs)


def violations(rules, lines, file_path):
    """Return ``(rule, offending_line)`` for each rule matching some line.

    A rule is reported once, on the first line it matches. A rule whose pattern
    does not compile is skipped rather than raised — one bad pattern must not
    take the whole registry down.
    """
    found = []
    for rule in rules:
        if not rule_applies(rule, file_path):
            continue
        try:
            regex = re.compile(rule["pattern"])
        except (re.error, TypeError, KeyError):
            continue
        for line in lines:
            if regex.search(line):
                found.append((rule, line))
                break
    return found


def deny_reason(found):
    """Render the ``permissionDecisionReason`` for the violated rules."""
    parts = ["This edit was blocked by shipd guardrails."]
    for rule, line in found:
        parts.append(
            "\n- %s: %s\n  offending line: %s"
            % (rule["name"], rule["message"], line.strip()))
    parts.append(
        "\nRewrite the edit without the flagged lines. To change the rules, "
        "see the `guardrails` key in the content directory's README.md.")
    return "".join(parts)


def deny(found):
    """Print the PreToolUse deny decision (guardrail-deny-output)."""
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": deny_reason(found),
    }}, sys.stdout)
    sys.stdout.write("\n")


def evaluate(payload):
    """Return the violations for ``payload``, or ``[]`` to allow the call."""
    tool_name = payload.get("tool_name")
    if tool_name not in ("Edit", "Write"):
        return []
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []
    lines = added_lines(tool_name, tool_input)
    if not lines:
        return []
    start = payload.get("cwd")
    if not isinstance(start, str) or not start:
        start = os.getcwd()
    rules = resolve_rules(start)
    if rules is None:
        return []
    return violations(rules, lines, tool_input.get("file_path"))


def main():
    if os.environ.get("SHIPD_GUARDRAILS") == "off":
        return 0
    try:
        payload = json.loads(sys.stdin.read())
    except (ValueError, OSError):
        return 0
    if not isinstance(payload, dict):
        return 0
    found = evaluate(payload)
    if found:
        deny(found)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # fail open: never break the user's editing
        sys.exit(0)
