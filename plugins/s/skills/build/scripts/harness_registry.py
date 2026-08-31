#!/usr/bin/env python3
"""harness_registry — the harness-adapter registry.

Declared data, not detection: every later generation step reads a harness's
identity, target paths, frontmatter dialect, and supported features from here
rather than probing the machine, so a repo without a harness installed still
generates for it, and a vendor that moves its command directory is a one-entry
edit.

The registry holds no prompt content. ``repo_pattern`` and ``user_dir`` are
*paths*, with ``{command}`` standing in for a command id; the bodies that fill
them live elsewhere.

Stdlib-only Python 3, per the engine's constitution.
"""

# The feature vocabulary a harness entry may declare. Deliberately coarse and
# small: a feature earns a name only when a command body would render
# differently for its absence.
FEATURES = (
    "subagents",
    "question-dialogs",
    "file-references",
    "background-tasks",
)

# One entry per supported harness. Keys, all required:
#
#   id           kebab-case, unique, the name every verb and path uses
#   name         display name, the vendor's own capitalization
#   repo_pattern repo-relative generated-file path carrying a ``{command}``
#                placeholder — or, for the ``conventions-file`` dialect, a
#                literal single-file path — or ``None`` for a harness with no
#                per-repo files
#   user_dir     the user-global command location, or ``None``
#   dialect      how a generated file carries its metadata: ``yaml``
#                frontmatter, ``markdown-headers``, or a single
#                ``conventions-file``
#   frontmatter  the field names the ``yaml`` dialect emits, in order; empty
#                for every other dialect
#   features     a subset of ``FEATURES``, in ``FEATURES`` order
#
# Plain dicts rather than dataclasses — the engine's existing style, and the
# registry stays trivially JSON-serializable for the CLI's ``--json``.
HARNESSES = (
    {
        "id": "claude-code",
        "name": "Claude Code",
        "repo_pattern": ".claude/commands/shipd/{command}.md",
        "user_dir": "~/.claude/commands/shipd/",
        "dialect": "yaml",
        "frontmatter": ("name", "description", "allowed-tools"),
        "features": ("subagents", "question-dialogs", "file-references",
                     "background-tasks"),
    },
    {
        "id": "cursor",
        "name": "Cursor",
        "repo_pattern": ".cursor/commands/shipd-{command}.md",
        "user_dir": "~/.cursor/commands/",
        "dialect": "yaml",
        "frontmatter": ("name", "id", "category", "description"),
        "features": ("file-references", "background-tasks"),
    },
    {
        "id": "github-copilot",
        "name": "GitHub Copilot",
        "repo_pattern": ".github/prompts/shipd-{command}.prompt.md",
        "user_dir": None,
        "dialect": "yaml",
        "frontmatter": ("description",),
        "features": ("file-references",),
    },
    {
        "id": "windsurf",
        "name": "Windsurf",
        "repo_pattern": ".windsurf/workflows/shipd-{command}.md",
        "user_dir": "~/.codeium/windsurf/global_workflows/",
        "dialect": "yaml",
        "frontmatter": ("description",),
        "features": ("file-references",),
    },
    {
        "id": "aider",
        "name": "Aider",
        # A literal path, not a per-command pattern: the `conventions-file`
        # dialect writes one whole-harness file the user wires into
        # `.aider.conf.yml` with `read:`.
        "repo_pattern": "shipd-conventions.md",
        "user_dir": None,
        "dialect": "conventions-file",
        "frontmatter": (),
        "features": (),
    },
    {
        "id": "codex",
        "name": "Codex",
        "repo_pattern": None,
        "user_dir": "~/.codex/prompts/",
        "dialect": "yaml",
        "frontmatter": ("description", "argument-hint"),
        "features": ("file-references",),
    },
    {
        "id": "cline",
        "name": "Cline",
        "repo_pattern": ".clinerules/workflows/shipd-{command}.md",
        "user_dir": None,
        "dialect": "markdown-headers",
        "frontmatter": (),
        "features": ("file-references",),
    },
    {
        "id": "roocode",
        "name": "Roo Code",
        "repo_pattern": ".roo/commands/shipd-{command}.md",
        "user_dir": None,
        "dialect": "markdown-headers",
        "frontmatter": (),
        "features": ("file-references",),
    },
    {
        "id": "continue",
        "name": "Continue",
        "repo_pattern": ".continue/prompts/shipd-{command}.prompt",
        "user_dir": None,
        "dialect": "yaml",
        "frontmatter": ("name", "description", "invokable"),
        "features": ("file-references",),
    },
    {
        "id": "antigravity",
        "name": "Antigravity",
        "repo_pattern": ".agent/workflows/shipd-{command}.md",
        "user_dir": None,
        "dialect": "yaml",
        "frontmatter": ("description",),
        "features": ("file-references",),
    },
    {
        "id": "devin",
        "name": "Devin",
        "repo_pattern": ".devin/workflows/shipd-{command}.md",
        "user_dir": None,
        "dialect": "yaml",
        "frontmatter": ("name", "description", "category", "tags"),
        "features": ("file-references",),
    },
    {
        "id": "oh-my-pi",
        "name": "oh-my-pi",
        "repo_pattern": ".omp/commands/shipd-{command}.md",
        "user_dir": None,
        "dialect": "yaml",
        "frontmatter": ("description",),
        "features": ("subagents", "file-references"),
    },
    {
        "id": "opencode",
        "name": "OpenCode",
        "repo_pattern": ".opencode/commands/shipd-{command}.md",
        "user_dir": "~/.config/opencode/commands/",
        "dialect": "yaml",
        "frontmatter": ("description",),
        "features": ("subagents", "file-references"),
    },
    {
        "id": "pi",
        "name": "Pi",
        "repo_pattern": ".pi/prompts/shipd-{command}.md",
        "user_dir": "~/.pi/agent/prompts/",
        "dialect": "yaml",
        "frontmatter": ("description", "argument-hint"),
        "features": ("file-references",),
    },
)


def get(harness_id):
    """The entry ``harness_id`` names, or ``None`` when no entry has that id."""
    for entry in HARNESSES:
        if entry["id"] == harness_id:
            return entry
    return None


def ids():
    """Every harness id, in registry order."""
    return tuple(entry["id"] for entry in HARNESSES)
