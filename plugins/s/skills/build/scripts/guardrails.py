#!/usr/bin/env python3
"""guardrails.py — the guardrail hook (stdlib only, no network, no third-party
imports).

Claude Code invokes this script around every ``Edit`` and ``Write`` tool call,
handing it the hook payload as JSON on stdin. The script extracts the lines the
call would *add* and matches them against the resolved rule registry; which
rules it consults, and what a match produces, follows the payload's
``hook_event_name``:

- **PreToolUse** consults ``deny`` rules and prints a ``deny`` decision whose
  reason carries the violated rule's corrective message. The model reads that
  reason and retries differently, so the unwanted line never reaches the file.
- **PostToolUse** consults ``remind`` rules and prints the firing rules'
  messages as ``additionalContext``. The edit stands — the guidance simply
  reaches the model — so a remind rule fires at most once per session by
  default, or every ``cooldown`` seconds when it declares one.

Rules are markdown files — flat ``---`` frontmatter over a message body — read
from three sources in precedence order: the repo's ``<content-dir>/rules/`` in
each ancestor directory, the user's ``~/.shipd/rules/``, and the plugin's own
``hooks/rules/``, where the three built-ins live (change-log comments,
step-narration comments, placeholder comments). ``.shipd-config.json``'s
``guardrails`` key holds the kill-switches only: ``false`` turns the hook off,
``disable`` drops rules by name.

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
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# The recognized rule modes. ``deny`` blocks the call before it runs;
# ``remind`` lets it land and injects the message afterwards.
MODES = ("deny", "remind")

# The plugin's own built-in rule files, resolved relative to this script so the
# hook finds them from whatever cache snapshot it is running out of. The script
# carries no rule content of its own (guardrail-default-rules).
PLUGIN_RULES_DIR = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "hooks", "rules"))

# The user's cross-repository rulebook, and where remind cooldown state lives.
USER_SHIPD_DIR = "~/.shipd"


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


def resolved_config(start):
    """Return the layered configuration resolved for ``start``, or ``{}``.

    Resolution is the standard layered per-key merge (shipd-config
    layered-key-merge): the nearest ``.shipd-config.json`` declaring a key wins
    it wholesale. An unreadable layer or a malformed config file reads as no
    configuration at all — this hook never errors on config.
    """
    try:
        import spec_common
        config, _ = spec_common.resolve_config(start)
        return config if isinstance(config, dict) else {}
    except Exception:
        return {}


def content_dirname(config):
    """Return the content-directory name a resolved config names, defaulting to
    ``.shipd`` when the ``dir`` key is absent or malformed."""
    try:
        import spec_common
        return spec_common.specs_dirname(config)
    except Exception:
        return ".shipd"


def parse_frontmatter(text):
    """Split a rule file's ``text`` into its frontmatter fields and its body.

    The frontmatter is the block between the opening ``---`` line and the next
    ``---`` line, read as flat ``key: value`` pairs split on the first colon
    with both sides stripped; a line carrying no colon is ignored. Returns
    ``(fields, body)``, or ``None`` when the text does not open with ``---`` or
    the block is never closed. The format stays deliberately flat: the engine
    is stdlib-only, so there is no YAML parser to lean on.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() != "---":
            continue
        fields = {}
        for line in lines[1:index]:
            key, sep, value = line.partition(":")
            if sep:
                fields[key.strip()] = value.strip()
        return fields, "\n".join(lines[index + 1:])
    return None


def parse_rule_file(path):
    """Return the rule ``path`` declares, or ``None`` when it declares none
    (guardrail-rulebook-format).

    The rule's name is the filename stem. ``pattern`` is required and must
    compile, the body after the frontmatter is the corrective message and must
    be non-empty, ``mode`` defaults to ``deny`` and must otherwise name a
    recognized mode, ``files`` is a comma-separated glob list, and ``cooldown``
    is a positive whole number of seconds. Anything else — an unreadable file,
    absent or unclosed frontmatter, a malformed field — skips the file, because
    one bad rule must never take the rulebook down with it.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    parsed = parse_frontmatter(text)
    if parsed is None:
        return None
    fields, body = parsed
    pattern = fields.get("pattern")
    message = body.strip()
    if not pattern or not message:
        return None
    try:
        re.compile(pattern)
    except re.error:
        return None
    mode = fields.get("mode") or "deny"
    if mode not in MODES:
        return None
    rule = {
        "name": os.path.splitext(os.path.basename(path))[0],
        "pattern": pattern,
        "message": message,
        "mode": mode,
    }
    globs = [glob.strip() for glob in fields.get("files", "").split(",")]
    globs = [glob for glob in globs if glob]
    if globs:
        rule["files"] = globs
    declared_cooldown = fields.get("cooldown")
    if declared_cooldown:
        try:
            cooldown = int(declared_cooldown)
        except ValueError:
            return None
        if cooldown <= 0:
            return None
        rule["cooldown"] = cooldown
    return rule


def load_rules_dir(directory):
    """Return the rules declared by ``directory``'s ``*.md`` files, ordered by
    filename. A directory that is absent or cannot be listed contributes
    nothing."""
    try:
        names = sorted(name for name in os.listdir(directory)
                       if name.endswith(".md"))
    except OSError:
        return []
    rules = []
    for name in names:
        rule = parse_rule_file(os.path.join(directory, name))
        if rule is not None:
            rules.append(rule)
    return rules


def rules_dirs(start, dirname):
    """Return the rulebook directories governing ``start``, nearest first
    (guardrail-rulebook-discovery): every ancestor's ``<dirname>/rules`` walked
    parent-by-parent to the filesystem root, then the user's
    ``~/.shipd/rules``, then the plugin's own built-ins."""
    dirs = []
    current = os.path.abspath(start)
    while True:
        dirs.append(os.path.join(current, dirname, "rules"))
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    dirs.append(os.path.join(os.path.expanduser(USER_SHIPD_DIR), "rules"))
    dirs.append(PLUGIN_RULES_DIR)
    return dirs


def resolve_rules(start):
    """Return the rule registry governing ``start``, or ``None`` when the hook
    is turned off there (shipd-config guardrails-key).

    Walk the rulebook sources in precedence order, keeping the first rule to
    claim each name — so a repo rule overrides a user rule overrides a built-in
    — then drop every name the config's ``disable`` lists. Rule definitions
    live in the rulebook, never in configuration: a ``guardrails`` object's
    ``rules`` member, like any other unrecognized member, is ignored, and a
    value that is neither ``false`` nor an object reads as undeclared.
    """
    config = resolved_config(start)
    declared = config.get("guardrails")
    if declared is False:
        return None
    rules = []
    claimed = set()
    for directory in rules_dirs(start, content_dirname(config)):
        for rule in load_rules_dir(directory):
            if rule["name"] in claimed:
                continue
            claimed.add(rule["name"])
            rules.append(rule)
    disable = declared.get("disable") if isinstance(declared, dict) else None
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


def remind_text(found):
    """Render the ``additionalContext`` for the firing remind rules."""
    parts = ["shipd guardrails flagged this edit. It stands — but note:"]
    for rule, line in found:
        parts.append(
            "\n- %s: %s\n  flagged line: %s"
            % (rule["name"], rule["message"], line.strip()))
    parts.append(
        "\nCorrect the flagged lines in a follow-up edit where the note "
        "applies. To change the rules, see the `guardrails` key in the "
        "content directory's README.md.")
    return "".join(parts)


def remind(found):
    """Print the PostToolUse reminder (guardrail-remind-output)."""
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": remind_text(found),
    }}, sys.stdout)
    sys.stdout.write("\n")


def state_path(session_id):
    """Return the cooldown-state file for ``session_id``, or ``None`` when the
    payload names no usable session — a rule then fires without recording."""
    if not isinstance(session_id, str) or not session_id:
        return None
    if session_id in (".", "..") or "/" in session_id or os.sep in session_id:
        return None
    return os.path.join(os.path.expanduser(USER_SHIPD_DIR), "guardrails",
                        session_id + ".json")


def load_state(path):
    """Return the recorded last-fire times for a session, or ``{}``. Missing,
    unreadable, and malformed state all read as nothing recorded."""
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def save_state(path, state):
    """Record the last-fire times, best effort. A state directory that cannot
    be created or written is not worth failing an edit over: the reminder has
    already been delivered, and the worst outcome is that it repeats."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
    except (OSError, ValueError, TypeError):
        pass


def rule_is_due(rule, state, now):
    """Whether a remind rule may fire (guardrail-remind-output).

    A rule fires once per session by default; one declaring ``cooldown`` re-arms
    that many seconds after its last fire. A nonsense recorded time re-arms the
    rule rather than silencing it for the rest of the session.
    """
    last = state.get(rule["name"])
    if not isinstance(last, (int, float)) or isinstance(last, bool):
        return True
    cooldown = rule.get("cooldown")
    if not isinstance(cooldown, int):
        return False
    return now - last >= cooldown


def evaluate(payload, mode):
    """Return the ``mode`` rules ``payload`` violates, or ``[]``."""
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
    rules = [rule for rule in rules if rule.get("mode") == mode]
    return violations(rules, lines, tool_input.get("file_path"))


def run_remind(payload):
    """Deliver the reminders ``payload``'s remind rules earn, and record the
    fires against the session's cooldown state."""
    found = evaluate(payload, "remind")
    if not found:
        return
    path = state_path(payload.get("session_id"))
    state = load_state(path)
    now = time.time()
    due = [(rule, line) for rule, line in found
           if rule_is_due(rule, state, now)]
    if not due:
        return
    remind(due)
    if path is None:
        return
    for rule, _ in due:
        state[rule["name"]] = now
    save_state(path, state)


def run_deny(payload):
    """Deny ``payload`` when one of its deny rules fires."""
    found = evaluate(payload, "deny")
    if found:
        deny(found)


def main():
    if os.environ.get("SHIPD_GUARDRAILS") == "off":
        return 0
    try:
        payload = json.loads(sys.stdin.read())
    except (ValueError, OSError):
        return 0
    if not isinstance(payload, dict):
        return 0
    if payload.get("hook_event_name") == "PostToolUse":
        run_remind(payload)
    else:
        run_deny(payload)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # fail open: never break the user's editing
        sys.exit(0)
