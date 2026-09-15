#!/usr/bin/env python3
"""Structure tests for the `/s:review` skill's reference split.

`SKILL.md` used to carry every review-time concern inline, including three
sections that only fire on a condition (spec-aware review, `--json` machine
output, and PR posting). This module pins the split: those three sections
live under `references/`, `SKILL.md` names every file there by path, every
named path resolves, each reference states its own load condition, the
hot-path guidance (workflow, severity rubric, difftastic probe) stays inline,
and neither of the other two rubric surfaces (the copilot skill body and the
harness command body) points at a reference path that only resolves relative
to `${CLAUDE_PLUGIN_ROOT}`.

Pure text-structure assertions — no production module is imported, since the
thing under test is prose shape, not code.
"""

import glob
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW_SKILL_DIR = os.path.normpath(os.path.join(HERE, ".."))
PLUGIN_S_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

SKILL_MD = os.path.join(REVIEW_SKILL_DIR, "SKILL.md")
REFERENCES_DIR = os.path.join(REVIEW_SKILL_DIR, "references")
JSON_OUTPUT_MD = os.path.join(REFERENCES_DIR, "json-output.md")
COPILOT_SKILL_MD = os.path.join(
    PLUGIN_S_ROOT, "integrations", "copilot", "SKILL.md")
HARNESS_REVIEW_BODY = os.path.join(
    PLUGIN_S_ROOT, "harness", "bodies", "review.md")

# The finding taxonomy's two payload surfaces (review-taxonomy-parity). The
# harness reference ships to every harness declaring `file-references`, so it
# is reached from this tests directory via the plugin root, not the skill's
# own references/ directory.
HARNESS_REVIEW_MD = os.path.join(
    PLUGIN_S_ROOT, "harness", "references", "review.md")

# The full finding taxonomy both payload surfaces must accept.
ALL_TAXONOMY_VALUES = frozenset((
    "bug", "contract", "edge-case", "untouched-caller", "spec-coverage",
    "test-coverage", "security", "performance", "stability",
    "data-integrity",
))

# Matches the one line in a taxonomy site naming the finding field as
# `cohort`, `category`, or `kind` — whichever the file currently uses —
# followed by its `|`-separated list of quoted string values, e.g.
# `"cohort": "bug" | "contract" | ...,`. Scoped to these three candidate
# names so it never mismatches the neighbouring `"severity"` enum line.
TAXONOMY_FIELD_RE = re.compile(
    r'^\s*"(cohort|category|kind)":\s*(".*"),?\s*$')

# The five risk-lens triggers, named exactly as plan.md's Implementation
# section orders them. Every surface that carries the lenses inline must
# name each of these verbatim (case-insensitively) — this is deliberately a
# literal match, not a loose keyword search, because the plan fixes this
# exact naming as the shared vocabulary across all three surfaces.
TRIGGER_PHRASES = (
    "secret or credential exposure",
    "authorization boundary",
    "unbounded work",
    "resource release",
    "migration reversibility",
)

# Proxies for "the exposure severity floor is stated": a floor sentence puts
# the word `high` in the same neighbourhood as the trigger it floors. `re`'s
# DOTALL lets the window span a wrapped line; the window is generous (160
# chars) because the floor is a full clause, not an adjacent word.
_EXPOSURE_FLOOR_PATTERNS = (
    re.compile(r"(?is)(?:secret|credential).{0,160}\bhigh\b"),
    re.compile(r"(?is)\bhigh\b.{0,160}(?:secret|credential)"),
)
_AUTHZ_FLOOR_PATTERNS = (
    re.compile(r"(?is)authorization boundary.{0,160}\bhigh\b"),
    re.compile(r"(?is)\bhigh\b.{0,160}authorization boundary"),
)

MOVED_HEADINGS = (
    "## Machine output mode",
    "## Posting to a PR",
    "## Spec-aware review",
)

# Matches a reference path as SKILL.md is expected to name it, e.g.
# "${CLAUDE_PLUGIN_ROOT}/skills/review/references/spec-aware.md".
REFERENCE_PATH_RE = re.compile(
    r"\$\{CLAUDE_PLUGIN_ROOT\}/skills/review/references/([\w-]+\.md)")

REFERENCES_UNDER_SKILL_RE = re.compile(r"skills/review/references/")

# Matches one `## References` table row naming a reference file, capturing
# its filename and the "Load when" cell text, e.g.
# "| `${CLAUDE_PLUGIN_ROOT}/skills/review/references/spec-aware.md` | ... |".
TABLE_ROW_RE = re.compile(
    r"^\|\s*`?\$\{CLAUDE_PLUGIN_ROOT\}/skills/review/references/"
    r"([\w-]+\.md)`?\s*\|\s*(.+?)\s*\|\s*$",
    re.MULTILINE)

# Lowercased tokens too generic to count as evidence two sentences agree.
STOPWORDS = frozenset((
    "this", "that", "when", "only", "file", "reads", "skill", "which",
    "with", "been", "they", "from", "into",
))

MIN_SHARED_CONTENT_WORDS = 3


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _content_words(text):
    """Lowercased alphabetic tokens of length >= 4, minus STOPWORDS.

    Backticks and other punctuation fall out for free: only letter runs are
    matched, so "`--json`" yields "json" and "poster's" yields "poster".
    """
    return {
        word.lower()
        for word in re.findall(r"[A-Za-z]+", text)
        if len(word) >= 4 and word.lower() not in STOPWORDS
    }


def _reference_condition_sentence(path):
    """The paragraph directly under the level-1 title in a reference file.

    Same region `test_each_reference_opens_with_title_and_condition` already
    inspects: the non-blank lines after the title, up to the next blank
    line, joined into one string.
    """
    lines = _read(path).splitlines()
    title_idx = next(i for i, ln in enumerate(lines) if ln.strip())
    condition_lines = []
    for ln in lines[title_idx + 1:]:
        if not ln.strip():
            if condition_lines:
                break
            continue
        condition_lines.append(ln)
    return " ".join(condition_lines)


def _text_excluding_references_section(text):
    """`text` with its `## References` section removed.

    Used to confirm a trigger phrase is stated in the workflow itself, not
    only in the References table's summary row for `risk-lenses.md`.
    """
    lines = text.splitlines()
    result = []
    in_references = False
    for ln in lines:
        if ln.startswith("## References"):
            in_references = True
            continue
        if in_references:
            if ln.startswith("## "):
                in_references = False
            else:
                continue
        result.append(ln)
    return "\n".join(result)


def _missing_triggers(text):
    # Collapse all whitespace runs (including newlines) to a single space
    # before matching. Markdown reflows prose at ~80 columns, so a multi-word
    # trigger phrase can legitimately wrap across a line break even though
    # the prose states it perfectly well; without this normalization, a
    # cosmetic wrap reads as a missing trigger. Do not simplify this back to
    # a plain substring check on `text.lower()`.
    lowered = re.sub(r"\s+", " ", text.lower())
    return [phrase for phrase in TRIGGER_PHRASES if phrase not in lowered]


def _exposure_floor_stated(text):
    return (
        any(p.search(text) for p in _EXPOSURE_FLOOR_PATTERNS)
        and any(p.search(text) for p in _AUTHZ_FLOOR_PATTERNS)
    )


def _taxonomy_field_and_values(path):
    """The `--json` taxonomy line's field name and its quoted enum values.

    Returns `(field_name, frozenset_of_values)` for the one line in `path`
    matching `TAXONOMY_FIELD_RE` — the line naming the finding taxonomy as
    `cohort`, `category`, or `kind`, whichever the file currently uses.
    """
    text = _read(path)
    for line in text.splitlines():
        match = TAXONOMY_FIELD_RE.match(line)
        if match:
            field = match.group(1)
            values = frozenset(re.findall(r'"([\w-]+)"', match.group(2)))
            return field, values
    raise AssertionError(
        f"no cohort/category/kind taxonomy line found in {path}")


class SkillMdStructureTest(unittest.TestCase):
    """Assertions about `SKILL.md` itself."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(SKILL_MD)
        cls.lines = cls.text.splitlines()

    def test_under_line_ceiling(self):
        self.assertLess(
            len(self.lines), 300,
            "SKILL.md must stay under 300 lines once the references split "
            "out the condition-gated sections")

    def test_no_moved_headings_remain(self):
        for heading in MOVED_HEADINGS:
            self.assertNotIn(
                heading, self.text,
                f"{heading!r} should have moved to a reference file")

    def test_workflow_steps_stayed_inline(self):
        self.assertIn("## Workflow", self.text)
        self.assertIn("### 1. Map the change", self.text)
        self.assertIn("### 7. Check test coverage per finding", self.text)

    def test_severity_rubric_stayed_inline(self):
        self.assertIn("Severity rubric.", self.text)
        self.assertIn("**high**", self.text)
        self.assertIn("**medium**", self.text)
        self.assertIn("**low**", self.text)

    def test_difft_probe_stayed_inline(self):
        self.assertIn("command -v difft", self.text)

    def test_risk_lens_triggers_stated_inline(self):
        """All five triggers appear in the workflow, not only the table.

        `SKILL.md` can read a reference file, so a trigger named only in the
        `## References` table (and left implicit in the workflow) would let
        a reviewer who never opens `risk-lenses.md` miss it entirely — the
        opposite of the "always visible" design this change requires.
        """
        inline_text = _text_excluding_references_section(self.text)
        missing = _missing_triggers(inline_text)
        self.assertFalse(
            missing,
            f"trigger(s) not named inline in SKILL.md (outside the "
            f"References table): {missing}")

    def test_risk_lens_exposure_floor_stated(self):
        self.assertTrue(
            _exposure_floor_stated(self.text),
            "SKILL.md must state that a secret/credential exposure finding "
            "and an authorization-boundary finding both carry severity "
            "`high`")

    def test_every_reference_file_is_named(self):
        named = set(REFERENCE_PATH_RE.findall(self.text))
        on_disk = {
            os.path.basename(p)
            for p in glob.glob(os.path.join(REFERENCES_DIR, "*.md"))
        }
        missing = on_disk - named
        self.assertFalse(
            missing,
            f"reference file(s) not named in SKILL.md: {sorted(missing)}")

    def test_every_named_reference_path_resolves(self):
        named = set(REFERENCE_PATH_RE.findall(self.text))
        self.assertTrue(named, "SKILL.md should name at least one reference")
        for name in named:
            path = os.path.join(REFERENCES_DIR, name)
            self.assertTrue(
                os.path.isfile(path),
                f"SKILL.md names {name!r}, but {path} does not exist")


class ReferenceFileStructureTest(unittest.TestCase):
    """Each file under `references/` states its own trigger up front."""

    def test_each_reference_opens_with_title_and_condition(self):
        paths = sorted(glob.glob(os.path.join(REFERENCES_DIR, "*.md")))
        self.assertTrue(paths, "expected at least one reference file")
        for path in paths:
            with self.subTest(path=path):
                lines = [ln for ln in _read(path).splitlines()]
                non_blank = [ln for ln in lines if ln.strip()]
                self.assertTrue(non_blank, f"{path} is empty")
                self.assertRegex(
                    non_blank[0], r"^# \S",
                    f"{path} must open with a level-1 title")
                self.assertFalse(
                    non_blank[0].startswith("## "),
                    f"{path} title must be level-1, not level-2")
                rest = "\n".join(non_blank[1:3])
                self.assertRegex(
                    rest, r"[Rr]eads this file",
                    f"{path} must state its load condition directly under "
                    "the title")


class OtherRubricSurfacesUntouchedTest(unittest.TestCase):
    """The copilot skill and the harness review body stay reference-free."""

    def test_copilot_skill_names_no_reference_path(self):
        text = _read(COPILOT_SKILL_MD)
        self.assertNotRegex(text, REFERENCES_UNDER_SKILL_RE)

    def test_harness_review_body_names_no_reference_path(self):
        text = _read(HARNESS_REVIEW_BODY)
        self.assertNotRegex(text, REFERENCES_UNDER_SKILL_RE)


class ReferenceFreeSurfacesCarryRiskLensesTest(unittest.TestCase):
    """The harness body and the copilot template carry the lenses inline.

    Neither surface can read `references/risk-lenses.md` — the harness body
    ships into other repositories with no `${CLAUDE_PLUGIN_ROOT}`, and the
    copilot template is vendored byte-for-byte into a GitHub Actions runner —
    so both must name all five triggers and the exposure floor in their own
    body text.
    """

    def test_harness_review_body_names_all_triggers_and_floor(self):
        text = _read(HARNESS_REVIEW_BODY)
        missing = _missing_triggers(text)
        self.assertFalse(
            missing,
            f"trigger(s) not named in the harness review body: {missing}")
        self.assertTrue(
            _exposure_floor_stated(text),
            "the harness review body must state the exposure severity "
            "floor for secret/credential and authorization-boundary "
            "findings")

    def test_copilot_skill_names_all_triggers_and_floor(self):
        text = _read(COPILOT_SKILL_MD)
        missing = _missing_triggers(text)
        self.assertFalse(
            missing,
            f"trigger(s) not named in the copilot skill template: {missing}")
        self.assertTrue(
            _exposure_floor_stated(text),
            "the copilot skill template must state the exposure severity "
            "floor for secret/credential and authorization-boundary "
            "findings")


class JsonOutputTaxonomyTest(unittest.TestCase):
    """The `--json` finding taxonomy grows the four risk-lens values."""

    def test_category_enum_accepts_lens_values(self):
        text = _read(JSON_OUTPUT_MD)
        line = next(
            (ln for ln in text.splitlines() if '"category":' in ln), None)
        self.assertIsNotNone(
            line, "expected a `\"category\":` line in json-output.md")
        for value in ("security", "performance", "stability",
                      "data-integrity"):
            self.assertIn(
                f'"{value}"', line,
                f"category enum is missing {value!r}: {line!r}")


class TaxonomyFieldParityTest(unittest.TestCase):
    """Both `--json` taxonomy surfaces name the field `category` and agree.

    `cohort` names only the architectural grouping `semdiff files` emits and
    `kind` names only a file's added/deleted/modified state in `semdiff
    diff` — neither may double as the finding taxonomy's field name. The two
    taxonomy sites (the plugin skill reference and the harness reference
    that ships to every harness declaring `file-references`) must also agree
    on the exact set of accepted values, since a value added to one alone
    would silently skip the other.
    """

    @classmethod
    def setUpClass(cls):
        cls.json_field, cls.json_values = _taxonomy_field_and_values(
            JSON_OUTPUT_MD)
        cls.harness_field, cls.harness_values = _taxonomy_field_and_values(
            HARNESS_REVIEW_MD)

    def test_json_output_names_the_field_category(self):
        self.assertEqual(
            self.json_field, "category",
            f"{JSON_OUTPUT_MD} names the taxonomy field "
            f"{self.json_field!r}, expected 'category'")

    def test_harness_reference_names_the_field_category(self):
        self.assertEqual(
            self.harness_field, "category",
            f"{HARNESS_REVIEW_MD} names the taxonomy field "
            f"{self.harness_field!r}, expected 'category'")

    def test_neither_site_names_the_field_cohort_or_kind(self):
        for path, field in (
            (JSON_OUTPUT_MD, self.json_field),
            (HARNESS_REVIEW_MD, self.harness_field),
        ):
            with self.subTest(path=path):
                self.assertNotIn(
                    field, ("cohort", "kind"),
                    f"{path} still names the finding taxonomy {field!r}")

    def test_value_sets_are_exactly_equal(self):
        symmetric_diff = self.json_values ^ self.harness_values
        self.assertFalse(
            symmetric_diff,
            "taxonomy value sets disagree between "
            f"{JSON_OUTPUT_MD} and {HARNESS_REVIEW_MD}: "
            f"symmetric difference {sorted(symmetric_diff)}")

    def test_value_set_contains_all_ten_values(self):
        missing = ALL_TAXONOMY_VALUES - self.json_values
        self.assertFalse(
            missing,
            f"{JSON_OUTPUT_MD} taxonomy is missing values: "
            f"{sorted(missing)}")


class TableConditionAgreementTest(unittest.TestCase):
    """Pins agreement between a `## References` table cell and its file.

    The table's "Load when" cell is a summary a reviewer reads without
    opening the reference; the reference file states the same condition in
    full. If the cell drifts from the file (as it once did for
    spec-aware.md, dropping the auto-trigger half of the rule), a reader who
    trusts only the table misses the real trigger. This does not require the
    two texts match exactly — only that they share enough substantive
    vocabulary to be recognizably the same condition.
    """

    def test_table_cell_agrees_with_reference_condition(self):
        table_rows = TABLE_ROW_RE.findall(_read(SKILL_MD))
        self.assertTrue(
            table_rows, "expected at least one reference row in the "
            "SKILL.md References table")
        for name, cell in table_rows:
            with self.subTest(reference=name):
                path = os.path.join(REFERENCES_DIR, name)
                sentence = _reference_condition_sentence(path)
                cell_words = _content_words(cell)
                sentence_words = _content_words(sentence)
                shared = cell_words & sentence_words
                self.assertGreaterEqual(
                    len(shared), MIN_SHARED_CONTENT_WORDS,
                    f"{name}: table cell {cell!r} shares only "
                    f"{sorted(shared)} with its file's condition sentence "
                    f"{sentence!r} — need at least "
                    f"{MIN_SHARED_CONTENT_WORDS} shared content words")


class PostingDefaultInvertedTest(unittest.TestCase):
    """Posting fires by default once a pull request is in scope, not only on
    an explicit request. Pinned against both the `SKILL.md` References table
    row for `posting.md` and that file's own condition sentence, so neither
    surface can drift back to gating on an explicit ask.
    """

    def test_table_row_and_condition_state_pull_request_default(self):
        table_rows = TABLE_ROW_RE.findall(_read(SKILL_MD))
        row = next(
            (cell for name, cell in table_rows if name == "posting.md"),
            None)
        self.assertIsNotNone(
            row, "expected a References table row for posting.md")
        posting_path = os.path.join(REFERENCES_DIR, "posting.md")
        condition = _reference_condition_sentence(posting_path)
        for text, label in (
            (row, "SKILL.md References table row for posting.md"),
            (condition, "posting.md condition sentence"),
        ):
            lowered = text.lower()
            self.assertIn(
                "pull request", lowered,
                f"{label} must state the file is read when a pull request "
                f"is in scope: {text!r}")
            self.assertNotIn(
                "explicitly requested", lowered,
                f"{label} must not gate on posting being explicitly "
                f"requested: {text!r}")


class ReferenceFreeSurfacesPostingDefaultTest(unittest.TestCase):
    """The two surfaces that cannot read `posting.md` — the harness review
    body and the harness review reference — carry the posting-default
    inversion in their own prose: a named pull request is posted to by
    default, and dispositioning the findings is asked for rather than
    automatic. Neither may still gate posting on an explicit request.
    """

    _NEGATIVE_PHRASES = (
        "post only when the user explicitly asks",
        "Post only on an explicit request",
    )

    def test_neither_surface_gates_posting_on_an_explicit_request(self):
        for path in (HARNESS_REVIEW_BODY, HARNESS_REVIEW_MD):
            with self.subTest(path=path):
                text = _read(path)
                for phrase in self._NEGATIVE_PHRASES:
                    self.assertNotIn(
                        phrase, text,
                        f"{path} must not gate posting on an explicit "
                        f"request: found {phrase!r}")

    def test_both_state_the_default_and_the_opt_in_disposition(self):
        for path in (HARNESS_REVIEW_BODY, HARNESS_REVIEW_MD):
            with self.subTest(path=path):
                lowered = re.sub(r"\s+", " ", _read(path).lower())
                self.assertIn(
                    "pull request", lowered,
                    f"{path} must name the pull request it posts to")
                self.assertIn(
                    "by default", lowered,
                    f"{path} must state that posting to a named pull "
                    f"request happens by default")
                self.assertIn(
                    "disposition", lowered,
                    f"{path} must state that dispositioning the findings "
                    f"is opt-in, asked for rather than automatic")


if __name__ == "__main__":
    unittest.main()
