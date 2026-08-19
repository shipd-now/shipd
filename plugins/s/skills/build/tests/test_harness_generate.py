#!/usr/bin/env python3
"""Tests for the harness generation engine — ``harness_generate.py``.

Two layers. The *rendering* tests below pin the dialect contract: which
frontmatter fields each harness's entry produces, the fixed value table
behind them, the YAML escaping, the ownership marker's position, and the
extension the surface pattern dictates. They render against the shipped
``plugins/s/harness/`` tree — unlike ``test_harness_bodies.py``, whose
fixtures pin the *renderer's* mechanics — because what is under test here is
exactly the pairing of the real registry entries with the real body
templates.

Nothing in this file writes to the shipped tree: rendering returns strings,
and the action tests that follow work inside temp roots with isolated
``HOME``s.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
PLUGIN_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
BIN = os.path.join(PLUGIN_ROOT, "bin", "shipd")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import harness_bodies as hb  # noqa: E402
import harness_generate as hg  # noqa: E402
import harness_registry as hr  # noqa: E402

# A stand-in for the refs root a real action computes, so a rendering test
# never depends on where the suite happens to run.
REFS = ".shipd/harness/references"

# The authored partials behind the `conventions-file` dialect, read from the
# shipped tree so the tests compare the render against its actual source.
BODIES = os.path.join(PLUGIN_ROOT, "harness", "bodies")


def partial(name):
    with open(os.path.join(BODIES, "%s.md" % name), encoding="utf-8") as fh:
        return fh.read()

_FIELD_RE = re.compile(r"^(?P<field>[A-Za-z0-9_-]+):(?: (?P<value>.*))?$")

# A plain (unquoted) YAML scalar this generator is willing to emit: no colon,
# no leading indicator character, no surrounding space. Anything else must
# arrive double-quoted.
_PLAIN_RE = re.compile(r"^[A-Za-z0-9_/.][^:#]*$")


def frontmatter(text):
    """``[(field, raw value)]`` of ``text``'s leading ``---`` block, or
    ``None`` when it carries none."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None
    fields = []
    for line in lines[1:]:
        if line == "---":
            return fields
        match = _FIELD_RE.match(line)
        assert match is not None, "unparseable frontmatter line %r" % line
        fields.append((match.group("field"), match.group("value") or ""))
    raise AssertionError("unterminated frontmatter block")


def body_lines(text):
    """``text``'s lines after its frontmatter block, or all of them when it
    has none."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return lines
    return lines[lines.index("---", 1) + 1:]


class YamlScalarTest(unittest.TestCase):
    """The escaper, exercised directly — the shipped descriptions cover only
    a few of its cases."""

    def test_plain_values_stay_bare(self):
        for value in ("shipd-plan", "shipd", "true", "Converge context."):
            with self.subTest(value=value):
                self.assertEqual(hg.yaml_scalar(value), value)

    def test_a_colon_forces_quoting(self):
        self.assertEqual(hg.yaml_scalar("Read `/s:remember` first."),
                         '"Read `/s:remember` first."')
        self.assertEqual(hg.yaml_scalar("key: value"), '"key: value"')

    def test_leading_indicators_force_quoting(self):
        for value in ("[input]", "- dash", "#hash", "*star", "&anchor",
                      "@at", "!bang", "%percent", ">fold", "|pipe",
                      "{brace}", "'quote'"):
            with self.subTest(value=value):
                self.assertTrue(hg.yaml_scalar(value).startswith('"'),
                                hg.yaml_scalar(value))

    def test_surrounding_space_and_emptiness_force_quoting(self):
        self.assertEqual(hg.yaml_scalar(""), '""')
        self.assertEqual(hg.yaml_scalar(" lead"), '" lead"')
        self.assertEqual(hg.yaml_scalar("trail "), '"trail "')

    def test_quotes_and_backslashes_are_escaped(self):
        self.assertEqual(hg.yaml_scalar('say "hi": now'),
                         '"say \\"hi\\": now"')
        self.assertEqual(hg.yaml_scalar("back\\slash: yes"),
                         '"back\\\\slash: yes"')


class YamlDialectTest(unittest.TestCase):
    def render(self, harness_id, command="plan"):
        return hg.render(hr.get(harness_id), command, refs=REFS)

    def test_cursor_carries_exactly_its_declared_fields(self):
        fields = frontmatter(self.render("cursor"))
        self.assertIsNotNone(fields)
        self.assertEqual([field for field, _value in fields],
                         ["name", "id", "category", "description"])
        values = dict(fields)
        self.assertEqual(values["name"], "shipd-plan")
        self.assertEqual(values["id"], "shipd-plan")
        self.assertEqual(values["category"], "shipd")
        self.assertEqual(values["description"], hb.description("plan"))

    def test_github_copilot_carries_only_description(self):
        fields = frontmatter(self.render("github-copilot"))
        self.assertEqual([field for field, _value in fields], ["description"])
        self.assertEqual(fields[0][1], hb.description("plan"))

    def test_a_field_with_no_declared_value_is_omitted(self):
        # claude-code declares `allowed-tools`; the fixed value table has no
        # entry for it, so it is left out rather than emitted empty.
        self.assertIn("allowed-tools", hr.get("claude-code")["frontmatter"])
        fields = frontmatter(self.render("claude-code"))
        self.assertEqual([field for field, _value in fields],
                         ["name", "description"])

    def test_the_fixed_value_table_covers_every_declared_field(self):
        declared = set()
        for entry in hr.HARNESSES:
            declared.update(entry["frontmatter"])
        emitted = set()
        for entry in hr.HARNESSES:
            if entry["dialect"] != "yaml":
                continue
            fields = frontmatter(hg.render(entry, "plan", refs=REFS))
            emitted.update(field for field, _value in fields)
        # Exactly one declared field is deliberately unvalued.
        self.assertEqual(declared - emitted, {"allowed-tools"})

    def test_codex_argument_hint_is_the_fixed_hint(self):
        values = dict(frontmatter(self.render("codex")))
        self.assertEqual(values["argument-hint"], '"[input]"')

    def test_continue_invokable_is_an_unquoted_boolean(self):
        values = dict(frontmatter(self.render("continue")))
        self.assertEqual(values["invokable"], "true")

    def test_devin_tags_are_the_fixed_namespace(self):
        values = dict(frontmatter(self.render("devin")))
        self.assertEqual(values["tags"], "shipd")
        self.assertEqual(values["category"], "shipd")

    def test_every_emitted_value_is_plain_or_quoted(self):
        for entry in hr.HARNESSES:
            if entry["dialect"] != "yaml":
                continue
            for command in hb.commands():
                fields = frontmatter(hg.render(entry, command, refs=REFS))
                for field, value in fields:
                    with self.subTest(harness=entry["id"], command=command,
                                      field=field):
                        if value.startswith('"'):
                            self.assertTrue(value.endswith('"'), value)
                        else:
                            self.assertRegex(value, _PLAIN_RE)

    def test_a_shipped_description_carrying_a_colon_is_quoted(self):
        # `forget`'s description names `/s:remember`; the generator quotes on
        # any colon, so this is the shipped tree's own escaping case.
        self.assertIn(":", hb.description("forget"))
        values = dict(frontmatter(self.render("cursor", "forget")))
        self.assertEqual(values["description"],
                         '"%s"' % hb.description("forget"))

    def test_the_marker_is_the_first_line_after_the_frontmatter(self):
        lines = body_lines(self.render("cursor"))
        self.assertEqual(lines[0], hg.MARKER)

    def test_the_rendered_body_follows(self):
        text = self.render("cursor")
        expected = hb.render("plan", hr.get("cursor")["features"],
                             refs_dir=REFS)
        self.assertTrue(text.endswith(expected), text[-200:])


class MarkdownHeadersDialectTest(unittest.TestCase):
    def test_cline_has_no_frontmatter_and_leads_with_the_header(self):
        text = hg.render(hr.get("cline"), "plan", refs=REFS)
        self.assertIsNone(frontmatter(text))
        self.assertNotIn("---\n", text.split("\n\n")[0])
        lines = text.splitlines()
        self.assertEqual(lines[0], "# shipd-plan")
        self.assertEqual(lines[1], hb.description("plan"))
        self.assertEqual(lines[2], "")
        self.assertEqual(lines[3], hg.MARKER)

    def test_roocode_renders_the_same_dialect(self):
        text = hg.render(hr.get("roocode"), "status", refs=REFS)
        self.assertTrue(text.startswith("# shipd-status\n"), text[:80])
        self.assertIn(hg.MARKER, text)

    def test_the_rendered_body_follows(self):
        text = hg.render(hr.get("cline"), "plan", refs=REFS)
        expected = hb.render("plan", hr.get("cline")["features"],
                             refs_dir=REFS)
        self.assertTrue(text.endswith(expected), text[-200:])


class ConventionsDialectTest(unittest.TestCase):
    """The single-file dialect: one whole-harness document, not one file per
    command, so the command set arrives as an index rather than as files."""

    def render(self):
        return hg.render(hr.get("aider"))

    def test_the_marker_leads_the_file(self):
        self.assertTrue(self.render().startswith(hg.MARKER + "\n"),
                        self.render()[:120])

    def test_no_placeholder_survives(self):
        text = self.render()
        for placeholder in ("{preamble}", "{command_index}", "{refs}"):
            with self.subTest(placeholder=placeholder):
                self.assertNotIn(placeholder, text)

    def test_every_command_is_indexed_with_its_description(self):
        text = self.render()
        for command in hb.commands():
            with self.subTest(command=command):
                self.assertIn("- shipd-%s — %s"
                              % (command, hb.description(command)), text)

    def test_the_preamble_is_spliced_in_whole(self):
        text = self.render()
        self.assertIn(partial("_preamble").strip(), text)
        # The preamble's engine-scripts snippet is what makes the file usable.
        self.assertIn(".claude/plugins/cache/shipd/s", text)

    def test_the_authored_prose_survives(self):
        text = self.render()
        # The two flat substitutions are the only edits: the template's own
        # opening line and its `.aider.conf.yml` wiring note come through.
        source = partial("_conventions")
        self.assertIn(source.splitlines()[0], text)
        self.assertIn("read: shipd-conventions.md", text)

    def test_no_frontmatter_and_no_command_heading(self):
        text = self.render()
        self.assertIsNone(frontmatter(text))
        self.assertNotIn("# shipd-plan\n", text)


class RenderDialectRefusalTest(unittest.TestCase):
    def test_a_dialect_with_no_renderer_is_refused(self):
        # Every dialect the registry declares now renders; the refusal is the
        # guard on adding a fourth without a renderer, so it is exercised
        # against a fabricated entry rather than a shipped one.
        entry = dict(hr.get("cline"), id="invented", dialect="toml-preamble")
        with self.assertRaises(ValueError) as caught:
            hg.render(entry, "plan", refs=REFS)
        self.assertIn("toml-preamble", str(caught.exception))


class SurfaceTest(unittest.TestCase):
    def test_the_extension_follows_the_repo_pattern(self):
        cases = {
            "cursor": ".cursor/commands/shipd-plan.md",
            "github-copilot": ".github/prompts/shipd-plan.prompt.md",
            "continue": ".continue/prompts/shipd-plan.prompt",
            "claude-code": ".claude/commands/shipd/plan.md",
        }
        for harness_id, expected in cases.items():
            with self.subTest(harness=harness_id):
                self.assertEqual(hg.repo_relpath(hr.get(harness_id), "plan"),
                                 os.path.normpath(expected))

    def test_a_harness_without_a_repo_pattern_has_no_repo_surface(self):
        self.assertIsNone(hg.repo_relpath(hr.get("codex"), "plan"))

    def test_the_conventions_surface_is_one_whole_harness_file(self):
        entry = hr.get("aider")
        self.assertEqual(hg.command_paths(entry, hg.REPO_MODE, "/tmp/root"),
                         ["/tmp/root/shipd-conventions.md"])

    def test_the_user_basename_follows_the_repo_pattern_when_there_is_one(self):
        self.assertEqual(
            os.path.basename(hg.user_path(hr.get("cursor"), "plan")),
            "shipd-plan.md")
        # Claude Code's pattern already namespaces under `shipd/`, so its
        # basename is the bare command.
        self.assertEqual(
            os.path.basename(hg.user_path(hr.get("claude-code"), "plan")),
            "plan.md")

    def test_a_pattern_less_harness_gets_the_default_user_basename(self):
        self.assertEqual(
            os.path.basename(hg.user_path(hr.get("codex"), "plan")),
            "shipd-plan.md")

    def test_a_harness_without_a_user_dir_has_no_user_surface(self):
        for harness_id in ("github-copilot", "cline", "aider"):
            with self.subTest(harness=harness_id):
                self.assertIsNone(hg.user_path(hr.get(harness_id), "plan"))


# ---------------------------------------------------------------------------
# The file actions, driven through the real binary
# ---------------------------------------------------------------------------


class ActionTestCase(unittest.TestCase):
    """A temp repository root, a temp working directory, and an isolated
    ``HOME``, with the binary driven by path through a subprocess — the
    ``test_harness_registry.py`` style, so the exec bit and the argument
    parsing are exercised and every write the suite provokes lands in a
    directory it owns."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="shipd-generate-root-")
        self.cwd = tempfile.mkdtemp(prefix="shipd-generate-cwd-")
        self.home = tempfile.mkdtemp(prefix="shipd-generate-home-")

    def tearDown(self):
        for path in (self.home, self.cwd, self.root):
            shutil.rmtree(path, ignore_errors=True)

    def cli(self, *args):
        env = dict(os.environ)
        env["HOME"] = self.home
        env["NO_COLOR"] = "1"
        return subprocess.run([BIN, "harness", *args], capture_output=True,
                              text=True, cwd=self.cwd, env=env)

    def tree(self, base):
        """``{relative path: bytes}`` for every file under ``base``."""
        found = {}
        for current, _dirs, names in os.walk(base):
            for name in names:
                path = os.path.join(current, name)
                with open(path, "rb") as handle:
                    found[os.path.relpath(path, base)] = handle.read()
        return found

    def error_lines(self, result):
        return [line for line in result.stderr.splitlines() if line.strip()]

    def cursor_files(self):
        return sorted(os.path.join(".cursor", "commands",
                                   "shipd-%s.md" % command)
                      for command in hb.commands())

    def reference_files(self):
        return sorted(os.path.join(".shipd", "harness", "references",
                                   "%s.md" % command)
                      for command in hb.commands()
                      if hb.reference(command) is not None)


class AddTest(ActionTestCase):
    def test_add_writes_one_owned_file_per_command(self):
        result = self.cli("add", "cursor", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        written = self.tree(self.root)
        for relative in self.cursor_files():
            with self.subTest(path=relative):
                self.assertIn(relative, written)
                self.assertIn(hg.MARKER, written[relative].decode("utf-8"))

    def test_add_writes_the_reference_files_and_resolves_refs(self):
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        written = self.tree(self.root)
        for relative in self.reference_files():
            with self.subTest(path=relative):
                self.assertIn(relative, written)
                self.assertIn(hg.MARKER, written[relative].decode("utf-8"))
        # `initiative`'s body points at `{refs}/initiative.md`; the generated
        # file names the refs root that actually holds it.
        body = written[os.path.join(".cursor", "commands",
                                    "shipd-initiative.md")].decode("utf-8")
        self.assertIn(".shipd/harness/references/initiative.md", body)
        for relative, data in written.items():
            with self.subTest(path=relative):
                self.assertNotIn("{refs}", data.decode("utf-8"))

    def test_re_running_add_changes_no_bytes(self):
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        before = self.tree(self.root)
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        self.assertEqual(self.tree(self.root), before)

    def test_user_mode_writes_only_under_home(self):
        result = self.cli("add", "codex", "--user")
        self.assertEqual(result.returncode, 0, result.stderr)
        prompts = os.path.join(self.home, ".codex", "prompts")
        self.assertTrue(os.path.isdir(prompts), result.stdout)
        for command in hb.commands():
            with self.subTest(command=command):
                self.assertTrue(os.path.isfile(
                    os.path.join(prompts, "shipd-%s.md" % command)))
        self.assertTrue(os.path.isdir(
            os.path.join(self.home, ".shipd", "harness", "references")))
        self.assertEqual(self.tree(self.cwd), {})
        self.assertEqual(self.tree(self.root), {})

    def test_user_mode_refs_are_named_from_home(self):
        self.assertEqual(self.cli("add", "codex", "--user").returncode, 0)
        with open(os.path.join(self.home, ".codex", "prompts",
                               "shipd-initiative.md"), encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("~/.shipd/harness/references/initiative.md", body)

    def test_a_modeless_harness_is_skipped_not_failed(self):
        # aider has a repo surface and no user-global one, so the skip path is
        # user mode.
        result = self.cli("add", "aider", "--user")
        self.assertEqual(result.returncode, 0, result.stderr)
        skipped = [line for line in result.stdout.splitlines()
                   if "skipped" in line and "aider" in line]
        self.assertEqual(len(skipped), 1, result.stdout)
        self.assertEqual(self.tree(self.home), {})
        self.assertEqual(self.tree(self.cwd), {})
        self.assertEqual(self.tree(self.root), {})

    def test_all_covers_every_harness_with_a_surface(self):
        result = self.cli("add", "--all", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        written = self.tree(self.root)
        for entry in hr.HARNESSES:
            relative = hg.repo_relpath(entry, "plan")
            with self.subTest(harness=entry["id"]):
                if relative is None:
                    self.assertIn("skipped", "".join(
                        line for line in result.stdout.splitlines()
                        if entry["id"] in line))
                else:
                    self.assertIn(relative, written)

    def test_no_selection_is_a_usage_error(self):
        for action in ("add", "remove"):
            with self.subTest(action=action):
                result = self.cli(action, "--root", self.root)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(self.tree(self.root), {})

    def test_an_unknown_id_is_a_single_error_line(self):
        result = self.cli("add", "no-such-harness", "--root", self.root)
        self.assertNotEqual(result.returncode, 0)
        lines = self.error_lines(result)
        self.assertEqual(len(lines), 1, result.stderr)
        self.assertTrue(lines[0].startswith("Error: "), lines[0])
        self.assertEqual(self.tree(self.root), {})


class ConventionsFileTest(ActionTestCase):
    """aider's whole-harness surface: exactly one generated file, and the one
    manual wiring step it still needs."""

    TARGET = "shipd-conventions.md"

    def test_add_writes_exactly_one_owned_file(self):
        result = self.cli("add", "aider", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        written = self.tree(self.root)
        self.assertEqual(sorted(written), [self.TARGET])
        self.assertIn(hg.MARKER, written[self.TARGET].decode("utf-8"))

    def test_add_reports_the_conf_wiring_step(self):
        result = self.cli("add", "aider", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        pointer = [line for line in result.stdout.splitlines()
                   if ".aider.conf.yml" in line]
        self.assertEqual(len(pointer), 1, result.stdout)
        self.assertIn("read: %s" % self.TARGET, pointer[0])

    def test_re_running_add_changes_no_bytes(self):
        self.assertEqual(self.cli("add", "aider", "--root",
                                  self.root).returncode, 0)
        before = self.tree(self.root)
        self.assertEqual(self.cli("add", "aider", "--root",
                                  self.root).returncode, 0)
        self.assertEqual(self.tree(self.root), before)

    def test_remove_deletes_the_owned_file_and_keeps_a_neighbor(self):
        self.assertEqual(self.cli("add", "aider", "--root",
                                  self.root).returncode, 0)
        neighbor = os.path.join(self.root, "CONVENTIONS.md")
        with open(neighbor, "w", encoding="utf-8") as handle:
            handle.write("my own conventions\n")
        result = self.cli("remove", "aider", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(self.tree(self.root)), ["CONVENTIONS.md"])

    def test_a_foreign_conventions_file_is_refused_without_force(self):
        path = os.path.join(self.root, self.TARGET)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("mine, not shipd's\n")
        result = self.cli("add", "aider", "--root", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.error_lines(result)), 1, result.stderr)
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "mine, not shipd's\n")

    def test_status_walks_absent_installed_stale(self):
        def state():
            result = self.cli("status", "aider", "--root", self.root, "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)["aider"]["state"]

        self.assertEqual(state(), "absent")
        self.assertEqual(self.cli("add", "aider", "--root",
                                  self.root).returncode, 0)
        self.assertEqual(state(), "installed")
        with open(os.path.join(self.root, self.TARGET), "a",
                  encoding="utf-8") as handle:
            handle.write("\nedited by hand\n")
        self.assertEqual(state(), "stale")


class OwnershipTest(ActionTestCase):
    TARGET = os.path.join(".cursor", "commands", "shipd-plan.md")
    FOREIGN = "my own notes, not shipd's\n"

    def plant(self):
        path = os.path.join(self.root, self.TARGET)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.FOREIGN)
        return path

    def test_a_foreign_target_is_refused_without_force(self):
        path = self.plant()
        result = self.cli("add", "cursor", "--root", self.root)
        self.assertNotEqual(result.returncode, 0)
        lines = self.error_lines(result)
        self.assertEqual(len(lines), 1, result.stderr)
        self.assertTrue(lines[0].startswith("Error: "), lines[0])
        self.assertIn(self.TARGET, lines[0])
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), self.FOREIGN)
        # The refusal is total: no sibling was written either.
        self.assertEqual(sorted(self.tree(self.root)), [self.TARGET])

    def test_force_rewrites_a_foreign_target(self):
        path = self.plant()
        result = self.cli("add", "cursor", "--root", self.root, "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(path, encoding="utf-8") as handle:
            self.assertIn(hg.MARKER, handle.read())
        self.assertEqual(sorted(self.tree(self.root)),
                         sorted(self.cursor_files() + self.reference_files()))


class RemoveTest(ActionTestCase):
    def test_remove_deletes_the_owned_files_and_keeps_a_neighbor(self):
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        neighbor = os.path.join(self.root, ".cursor", "commands", "mine.md")
        with open(neighbor, "w", encoding="utf-8") as handle:
            handle.write("mine\n")
        result = self.cli("remove", "cursor", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(self.tree(self.root)),
                         [os.path.join(".cursor", "commands", "mine.md")])

    def test_remove_prunes_the_directories_it_empties(self):
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        result = self.cli("remove", "cursor", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(self.root), {})
        self.assertFalse(os.path.exists(os.path.join(self.root, ".cursor")))
        self.assertFalse(os.path.exists(
            os.path.join(self.root, ".shipd", "harness")))

    def test_remove_leaves_a_foreign_target_alone(self):
        path = os.path.join(self.root, ".cursor", "commands", "shipd-plan.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("mine, not shipd's\n")
        result = self.cli("remove", "cursor", "--root", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.error_lines(result)), 1, result.stderr)
        self.assertTrue(os.path.isfile(path))

    def test_remove_all_empties_the_root(self):
        self.assertEqual(self.cli("add", "--all", "--root",
                                  self.root).returncode, 0)
        self.assertNotEqual(self.tree(self.root), {})
        self.assertEqual(self.cli("remove", "--all", "--root",
                                  self.root).returncode, 0)
        self.assertEqual(self.tree(self.root), {})

    def test_removing_what_was_never_added_is_not_an_error(self):
        result = self.cli("remove", "cursor", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree(self.root), {})


class StatusTest(ActionTestCase):
    def state_of(self, harness_id, *args):
        result = self.cli("status", "--root", self.root, "--json", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)[harness_id]["state"]

    def test_status_walks_absent_installed_stale(self):
        self.assertEqual(self.state_of("cursor"), "absent")
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        self.assertEqual(self.state_of("cursor"), "installed")
        target = os.path.join(self.root, ".cursor", "commands",
                              "shipd-plan.md")
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\nedited by hand\n")
        self.assertEqual(self.state_of("cursor"), "stale")

    def test_status_reports_a_foreign_target(self):
        path = os.path.join(self.root, ".cursor", "commands", "shipd-plan.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("mine\n")
        self.assertEqual(self.state_of("cursor"), "foreign")

    def test_status_reports_a_modeless_harness_as_skipped(self):
        # codex is user-global only, so it has nothing to report in repo mode.
        self.assertEqual(self.state_of("codex"), "skipped")

    def test_shared_references_do_not_make_another_harness_look_installed(self):
        # The refs root is shared, so cursor's install must leave every other
        # file-references harness reporting exactly `absent`.
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        self.assertEqual(self.state_of("claude-code"), "absent")

    def test_drifted_references_make_an_installed_harness_stale(self):
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        reference = os.path.join(self.root, ".shipd", "harness", "references",
                                 "plan.md")
        with open(reference, "a", encoding="utf-8") as handle:
            handle.write("\nedited by hand\n")
        self.assertEqual(self.state_of("cursor"), "stale")

    def test_status_writes_nothing(self):
        self.assertEqual(self.cli("add", "cursor", "--root",
                                  self.root).returncode, 0)
        before = self.tree(self.root)
        for args in (("status", "--root", self.root),
                     ("status", "--root", self.root, "--json"),
                     ("status", "cursor", "--root", self.root)):
            with self.subTest(args=args):
                self.assertEqual(self.cli(*args).returncode, 0)
        self.assertEqual(self.tree(self.root), before)

    def test_json_is_one_document_keyed_by_harness_id(self):
        result = self.cli("status", "--root", self.root, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(result.stdout)
        self.assertEqual(sorted(document), sorted(hr.ids()))
        for harness_id, record in document.items():
            with self.subTest(harness=harness_id):
                self.assertIn("state", record)

    def test_named_ids_narrow_the_report(self):
        result = self.cli("status", "cursor", "--root", self.root, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(json.loads(result.stdout)), ["cursor"])

    def test_the_text_report_names_the_state(self):
        result = self.cli("status", "cursor", "--root", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines()
                 if "cursor" in line]
        self.assertEqual(len(lines), 1, result.stdout)
        self.assertIn("absent", lines[0])


if __name__ == "__main__":
    unittest.main()
