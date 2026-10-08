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

Mostly pure text-structure assertions — no production module is imported for
them, since the thing under test is prose shape, not code. The one exception
is `SeverityDotParityTest`, which imports `review_gate` to pin the vendored
copilot workflow's severity-dot rendering against the real module rather than
a second hard-coded restatement of it.
"""

import glob
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW_SKILL_DIR = os.path.normpath(os.path.join(HERE, ".."))
PLUGIN_S_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

SKILL_MD = os.path.join(REVIEW_SKILL_DIR, "SKILL.md")
REFERENCES_DIR = os.path.join(REVIEW_SKILL_DIR, "references")
JSON_OUTPUT_MD = os.path.join(REFERENCES_DIR, "json-output.md")
PR_DESCRIPTION_MD = os.path.join(REFERENCES_DIR, "pr-description.md")
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

# The vendored posting workflow (review-skill): its inline Python carries
# its own copy of the severity-dot map and marker format, independent of
# `review_gate.py`. `SeverityDotParityTest` pins the two together.
COPILOT_GATE_YML = os.path.join(
    PLUGIN_S_ROOT, "integrations", "copilot", "copilot-review-gate.yml")

# `review_gate.py` itself, imported the way test_review_gate.py does, so
# `SeverityDotParityTest` reads its real `_SEV_DOT`/`_sev_marker` rather
# than a value copied here that could drift from either side unnoticed.
SCRIPTS = os.path.join(REVIEW_SKILL_DIR, "scripts")
sys.path.insert(0, SCRIPTS)
import review_gate  # noqa: E402

# The full finding taxonomy both payload surfaces must accept.
ALL_TAXONOMY_VALUES = frozenset((
    "bug", "contract", "edge-case", "untouched-caller", "spec-coverage",
    "test-coverage", "security", "performance", "stability",
    "data-integrity", "description-drift",
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
    "packaging and dependency manifests",
)

# The five new-code checks, named exactly as plan.md's Implementation
# section orders them. Every surface that carries the checks inline must
# name each of these verbatim (case-insensitively) — this is deliberately a
# literal match, not a loose keyword search, because the plan fixes this
# exact naming as the shared vocabulary across all surfaces.
NEW_CODE_CHECKS = (
    "wrong quantity measured",
    "escape hatch lapsing the guarantee",
    "termination on hostile input",
    "boundary agreement",
    "doc comment versus code",
)

# The checks whose detail moved into `call-site-tracing.md`. Same rule as
# NEW_CODE_CHECKS: the detail may live in a conditionally-loaded reference,
# but the name stays inline, so skipping the read costs guidance depth and
# never the check's existence.
DOWNSTREAM_CHECKS = (
    "untouched callers",
    "every match is a candidate",
    "misses extensionless scripts",
    "changed constants are contract changes",
    "uneven sibling sites",
)

CALL_SITE_VALUE_CHECKS = (
    "unreachable guard",
    "comment / intent vs. actual behaviour",
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

# Proxies for "the description check runs in both directions". The shipped
# v0.6.253 wording asked only for "verify every claim against the diff",
# which cannot reach an undersell: unmentioned scope has no claim to check,
# so a benchmark run matched the undersell case 0 times out of 3 in every
# configuration. Each surface must name the second direction explicitly.
_BOTH_DIRECTIONS_PATTERNS = (
    re.compile(r"(?is)both\s+directions"),
    re.compile(r"(?is)(?:never\s+mentions|does\s+not\s+mention|unmentioned)"),
)

# Proxies for "the rating rule is stated": severity follows what a defect
# does, never the kind of defect it is — otherwise a data-loss bug arriving
# as a "swallowed error" gets rated low, and low never blocks a merge. Each
# surface must say both that rating follows impact rather than kind, and
# that data loss reaches medium or high.
_IMPACT_FLOOR_PATTERNS = (
    # `[*_\s]+` so markdown emphasis around a word does not defeat the match.
    re.compile(
        r"(?is)what[*_\s]+the[*_\s]+defect[*_\s]+does,?[*_\s]+not[*_\s]+by"
        r"[*_\s]+the[*_\s]+kind[*_\s]+of[*_\s]+defect"),
    re.compile(r"(?is)data loss.{0,200}\b(?:medium|high)\b"),
)

MOVED_HEADINGS = (
    "## Machine output mode",
    "## Posting to a PR",
    "## Spec-aware review",
)

# Proxies for "the generalised further-location permission is stated, and the
# fix-site prohibition on a symptom is qualified by it rather than standing
# as a flat ban". `review-location-impact` generalised the rule already
# carried for `description-drift`'s further location so the location field's
# "fix site, never a symptom" parenthetical and the permission read as one
# rule rather than a contradiction a reviewer could read either reference or
# the inline surface and land on. `review-runtime-location` requires the
# permission to additionally cover the run-time shape — a site correct in
# isolation where the defect surfaces at run time — rather than the
# "independently shows the defect" wording that excluded it. The gap before
# "run time" is widened to 260 (from 220) because the run-time shape is now
# tied inline to the "conjunction of two lines neither wrong alone" clause
# that scopes it, which lengthens the sentence on both surfaces. `[*_\s]+`
# guards every join against markdown emphasis defeating the match.
_LOCATION_RULE_PATTERN = re.compile(
    r"(?is)fix[*_\s]+site.{0,40}(?:never|not)[*_\s]+(?:a[*_\s]+)?symptom"
    r".{0,140}further[*_\s]+(?:location|site).{0,260}run[*_\s]+time"
    r".{0,60}correct[*_\s]+in[*_\s]+isolation")

# The run-time shape's scope: it applies only where the defect is the
# conjunction of two lines, neither wrong alone (e.g. a manifest omission and
# the import that names it) — never to an ordinary single-cause bug's
# downstream symptom trace, which would otherwise satisfy "correct in
# isolation" and "surfaces at run time" just as easily. Pinned directly so a
# future edit cannot drop the scoping clause while leaving the run-time shape
# itself in place.
_RUNTIME_SHAPE_SCOPE_PATTERN = re.compile(
    r"(?is)conjunction[*_\s]+of[*_\s]+two[*_\s]+lines.{0,40}neither"
    r"[*_\s]+wrong[*_\s]+alone.{0,120}run[*_\s]+time")

# The specific exclusive wording that caused the regression this change
# fixes: a further location added *only* where the site independently shows
# the defect "on its own terms" — a predicate a correct import can never
# satisfy. Its absence is pinned directly (`test_skill_references.py`
# §review-runtime-location) rather than inferred from the new text's
# presence, because a reviewer could add the run-time shape alongside the
# old exclusive sentence and leave the exclusion intact.
_EXCLUSIVE_LOCATION_FORM_PATTERN = re.compile(
    r"(?is)further[*_\s]+(?:location|site).{0,40}only[*_\s]+where"
    r".{0,80}independently[*_\s]+shows[*_\s]+the[*_\s]+defect")

# The three concrete impact instances (review-location-impact), one pattern
# per instance, written loosely enough to match each surface's own wording
# (SKILL.md and the copilot template share phrasing; the harness body
# compresses it to fit its line ceiling) while still distinguishing the
# three from each other, per plan.md's Implementation section.
IMPACT_INSTANCE_PATTERNS = (
    re.compile(r"(?is)success[*_\s]+response.{0,20}hid(?:es|ing)[*_\s]+"
               r"(?:a[*_\s]+)?failure"),
    re.compile(r"(?is)cleanup.{0,20}drop(?:s|ping)[*_\s]+the[*_\s]+record"),
    re.compile(r"(?is)los(?:es|ing)[*_\s]+the[*_\s]+only[*_\s]+copy"),
)

# Proxy for "the no-drop rule is stated": uncertainty about severity is never
# grounds to omit a finding; report the best estimate and flag it uncertain
# instead. Measured on v0.6.261: edge-case findings fell 8 -> 2 over three
# rounds while test-coverage findings stayed flat at 4/4/4, and because the
# medium rubric already names an unhandled edge case, a re-rating would have
# moved them *up*, not away — they were being dropped, not re-rated.
_NO_DROP_RULE_PATTERN = re.compile(
    r"(?is)never.{0,70}(?:grounds[*_\s]+for[*_\s]+omitting[*_\s]+a[*_\s]+"
    r"finding|drop[*_\s]+a[*_\s]+finding).{0,100}best[*_\s]+estimate"
    r".{0,40}uncertain")

# The defect-kind words the old `low` bullet named on `SKILL.md` and the
# harness body, before this change moved the kinds list into the
# breadth-sweep step. A lowercased match of any of these inside the `low`
# bullet's own text means the kind list drifted back under `low`.
MOVED_KIND_WORDS = (
    "swallowed", "leak", "duplicated", "unread", "unstable", "blocking call",
)

# Matches from the `- **low**` bullet marker through the first occurrence of
# the word "findings" and the rest of that line — the bullet always ends
# "... are never findings[.,]...", so this captures exactly the bullet's own
# text without spilling into whatever rule or sentence follows it (which, on
# the harness body and the copilot template, sits on the very next line with
# no blank-line or bullet-marker boundary to stop a looser scan).
LOW_BULLET_RE = re.compile(r"-\s*\*\*low\*\*.*?\bfindings\b[^\n]*",
                           re.DOTALL | re.IGNORECASE)


def _low_bullet_text(text):
    match = LOW_BULLET_RE.search(text)
    if match is None:
        raise AssertionError("no '- **low**' bullet found")
    return match.group(0)

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


def _missing_checks(text):
    # Collapse all whitespace runs (including newlines) to a single space
    # before matching, using the same rationale as `_missing_triggers`.
    lowered = re.sub(r"\s+", " ", text.lower())
    return [check for check in NEW_CODE_CHECKS if check not in lowered]


def _missing_named(text, names):
    """Which of ``names`` are absent from ``text``, same matching as above."""
    lowered = re.sub(r"\s+", " ", text.lower())
    return [name for name in names if name not in lowered]


def _exposure_floor_stated(text):
    return (
        any(p.search(text) for p in _EXPOSURE_FLOOR_PATTERNS)
        and any(p.search(text) for p in _AUTHZ_FLOOR_PATTERNS)
    )


def _impact_floor_stated(text):
    return all(p.search(text) for p in _IMPACT_FLOOR_PATTERNS)


def _both_directions_stated(text):
    return all(p.search(text) for p in _BOTH_DIRECTIONS_PATTERNS)


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
        """SKILL.md's ceiling rose from 330 to 350, and now 350 to 370.

        Everything review-location-impact adds is a rule applied on every
        review, and the detail that could be extracted already has been —
        the new-code checks, the downstream checks, the call-site checks, the
        risk lenses. A measured defect (the location rule's contradiction
        between SKILL.md and a conditionally-read reference) showed an
        always-applies rule loses to the inline surface when it is deferred
        to a reference, so reflow and extraction cannot pay for this growth.
        The precedent is exact: the harness body's ceiling went 120 -> 140 in
        v0.6.254 for the same reason — "The ceiling guards against bloat; it
        is not a budget to compress real instructions into... A body that
        legitimately grows a step belongs under a raised ceiling, not under
        reworded instructions."

        review-related-file-context raises the ceiling again, from 350 to
        370: the new `related` workflow step is guidance that runs on every
        review, so it cannot be deferred to a conditionally-loaded reference,
        and SKILL.md sat at 340 of 350 before this change landed — too little
        headroom for the new step's own instructions. `review-skill-references`
        owns this figure; it is not restated anywhere else.
        """
        self.assertLess(
            len(self.lines), 370,
            "SKILL.md must stay under 370 lines once the references split "
            "out the condition-gated sections")

    def test_no_moved_headings_remain(self):
        for heading in MOVED_HEADINGS:
            self.assertNotIn(
                heading, self.text,
                f"{heading!r} should have moved to a reference file")

    def test_workflow_steps_stayed_inline(self):
        self.assertIn("## Workflow", self.text)
        self.assertIn("### 1. Map the change", self.text)
        self.assertIn("### 8. Check test coverage, rolled up per cohort",
                      self.text)

    def test_severity_rubric_stayed_inline(self):
        self.assertIn("Severity rubric.", self.text)
        self.assertIn("**high**", self.text)
        self.assertIn("**medium**", self.text)
        self.assertIn("**low**", self.text)

    def test_difft_probe_stayed_inline(self):
        self.assertIn("command -v difft", self.text)

    def test_base_freshness_block_stayed_inline(self):
        self.assertIn("Base freshness", self.text)

    def test_degradation_section_stops_rather_than_completes(self):
        """Difftastic is now required: a still-missing `difft` after the one
        `doctor --fix` attempt must stop the review, not complete it on the
        text engine."""
        match = re.search(r"^## Degradation\n(.*?)(?=\n## |\Z)", self.text,
                          re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(match, "no '## Degradation' section found")
        section = match.group(1)
        self.assertNotIn("Complete the review anyway", section)
        self.assertNotIn("never blocks a review", section)
        self.assertIn("stop", section.lower())
        self.assertIn("no verdict", section.lower())

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

    def test_new_code_checks_named_inline(self):
        """All five new-code checks appear in the workflow, not only the table.

        `SKILL.md` can read a reference file, so a check named only in the
        `## References` table (and left implicit in the workflow) would let
        a reviewer who never opens `new-code-checks.md` miss it entirely — the
        opposite of the "always visible" design this change requires.
        """
        inline_text = _text_excluding_references_section(self.text)
        missing = _missing_checks(inline_text)
        self.assertFalse(
            missing,
            f"check(s) not named inline in SKILL.md (outside the "
            f"References table): {missing}")

    def test_extracted_call_site_check_names_stay_inline(self):
        """The checks moved into `call-site-tracing.md` keep their names here.

        Same rule the risk lenses and the new-code checks already follow: a
        check that applies to every diff carrying the thing it inspects may
        defer its *detail* to a conditionally-loaded reference, but never its
        name — otherwise a reviewer who skips the read loses the check
        itself, not just the guidance behind it.
        """
        inline_text = _text_excluding_references_section(self.text)
        for label, names in (("downstream-impact", DOWNSTREAM_CHECKS),
                             ("call-site-value", CALL_SITE_VALUE_CHECKS)):
            with self.subTest(group=label):
                missing = _missing_named(inline_text, names)
                self.assertFalse(
                    missing,
                    f"{label} check(s) not named inline in SKILL.md "
                    f"(outside the References table): {missing}")

    def test_breadth_sweep_names_the_defect_kinds_itself(self):
        """The breadth-sweep step tells the reviewer what to look for.

        This change moves the kinds list out from under the severity
        rubric's `low` bullet and into the breadth-sweep step itself, so the
        step no longer points at the rubric for the list — it states a
        representative set of the kinds directly. A line-budget trim once
        dropped "end to end" from this step, so that phrasing is still
        pinned here too.
        """
        match = re.search(r"^### 6c\. [^\n]*\n(.*?)(?=\n### |\Z)", self.text,
                          re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(match, "no '### 6c.' breadth-sweep step found")
        section = match.group(1).lower()
        self.assertIn("end to end", section)
        for kind in ("swallowed", "leak", "dead or duplicated",
                     "never read", "unstable", "blocking call"):
            self.assertIn(
                kind, section,
                f"breadth-sweep step is missing defect kind {kind!r}")

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


class TestCoverageRollupTest(unittest.TestCase):
    """Both surfaces raise test-coverage findings per cohort, not per finding.

    Step 7 originally wrote one test-coverage finding for each finding, at
    every severity. That multiplies with the findings themselves: a
    benchmarking run measured 50 test-coverage findings across three rounds
    against 7 golden testing findings in the whole set, half of every low
    finding produced, burying the defects the step exists to flag.
    """

    def test_both_surfaces_roll_up_per_cohort(self):
        for path in (SKILL_MD, HARNESS_REVIEW_BODY):
            with self.subTest(path=path):
                text = re.sub(r"\s+", " ", _read(path).lower())
                # `[*_`\s]+` between words so markdown emphasis and code
                # ticks — "**one** `test-coverage` finding" — do not defeat
                # the match, the same trap the impact-floor patterns hit.
                self.assertRegex(
                    text,
                    r"one[*_`\s]+test-coverage[*_`\s]+finding[*_`\s]+per"
                    r"[*_`\s]+cohort",
                    f"{path} must raise one test-coverage finding per cohort")
                self.assertIn(
                    "never one per finding", text,
                    f"{path} must rule out the per-finding form explicitly")


class DescriptionCheckDirectionsTest(unittest.TestCase):
    """Every surface carrying the description check names both directions.

    Checking each claim against the diff finds contradictions and oversells.
    It cannot find an undersell: unmentioned scope has no claim to iterate
    over, so the pass has to run the other way too — the diff's substantial
    content against what the description is silent about. The first shipped
    wording asked only for the claim direction and matched the benchmark's
    undersell case 0 of 3 rounds in every configuration.

    `pr-description.md` carries the full method; `SKILL.md` and the harness
    body each have to name the second direction themselves, since a reader
    who never opens the reference would otherwise run one pass and believe
    the check complete.
    """

    def test_every_description_surface_names_both_directions(self):
        paths = (SKILL_MD, HARNESS_REVIEW_BODY,
                 os.path.join(REFERENCES_DIR, "pr-description.md"))
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(
                    _both_directions_stated(_read(path)),
                    f"{path} must name both directions of the description "
                    "check — each claim against the diff, and the diff's "
                    "substance against what the description never mentions")


class LocationRuleGeneralisedTest(unittest.TestCase):
    """The two reference-free surfaces state the generalised location rule.

    `review-skill`'s location field used to forbid a symptom site inline
    while `review-risk-lenses`'s packaging lens separately permitted one for
    a file-not-shipped finding — one requirement forbade what the other
    mandated. Measured on v0.6.261: the pg-pool finding named the second
    location in only 1 of 3 rounds, because the permission lived in a
    conditionally-read reference while the prohibition sat on the always-read
    surface. `review-location-impact` generalises the rule inline instead, so
    the fix-site prohibition and the further-location permission read as one
    rule on both surfaces that can read no reference file. The copilot
    template is excluded here on purpose — it carries no fix-site or symptom
    rule to begin with, so there is nothing for the generalisation to attach
    to.
    """

    def test_both_reference_free_surfaces_state_the_generalised_rule(self):
        """The permission must cover the run-time shape, not just symmetry.

        v0.6.262's wording required a further location to "independently
        show the defect on its own terms" — a predicate a correct import
        never satisfies, since the import itself is not wrong. Measured by
        benchy-cf over three rounds of the same three PRs, the pg-pool
        file-not-shipped finding named its second location in 1 of 3 rounds
        on v0.6.261 and 0 of 3 on v0.6.262: generalising the rule inline
        fixed the drift between surfaces but, applied literally, excluded
        the exact run-time site it was written to permit.
        """
        for path in (SKILL_MD, HARNESS_REVIEW_BODY):
            with self.subTest(path=path):
                self.assertRegex(
                    _read(path), _LOCATION_RULE_PATTERN,
                    f"{path} must state the fix-site prohibition on a "
                    "symptom together with the further-location permission, "
                    "not as an unqualified ban, and the permission must "
                    "cover the run-time shape — a site correct in isolation "
                    "where the defect surfaces at run time")

    def test_neither_surface_states_the_exclusive_form(self):
        """The regression's exact wording must not still be present.

        The old sentence — a further location added *only* where the site
        independently shows the defect on its own terms — is the specific
        wording that excluded the run-time site. Pinning its absence
        directly catches a rewording that adds the new shapes without
        dropping the old exclusion.
        """
        for path in (SKILL_MD, HARNESS_REVIEW_BODY):
            with self.subTest(path=path):
                self.assertNotRegex(
                    _read(path), _EXCLUSIVE_LOCATION_FORM_PATTERN,
                    f"{path} must not state that a further location is "
                    "added only where the site independently shows the "
                    "defect — that exclusive form is the wording that "
                    "excluded the run-time site")

    def test_description_drift_states_no_separate_exclusive_rule(self):
        """The description-drift case must rely on the general permission.

        The general further-location sentence says the packaging and
        description-drift cases rely on it "so no other requirement SHALL
        grant it separately" — but, until this test, three sites still
        granted the description-drift case its own separate, exclusive
        permission ("a further location added only where that site
        independently shows the drift"), the same disproven exclusive shape
        the general rule just dropped, just with "drift" in place of
        "defect". `_EXCLUSIVE_LOCATION_FORM_PATTERN` does not catch this
        variant, so it is pinned directly here across every surface that
        states the description-drift rule.
        """
        exclusive_drift_pattern = re.compile(
            r"(?is)only[*_\s]+where.{0,80}independently[*_\s]+shows"
            r"[*_\s]+the[*_\s]+drift")
        for path in (SKILL_MD, HARNESS_REVIEW_BODY, PR_DESCRIPTION_MD):
            with self.subTest(path=path):
                self.assertNotRegex(
                    _read(path), exclusive_drift_pattern,
                    f"{path} must not grant description-drift's further "
                    "location its own exclusive rule — it must rely on the "
                    "general further-location permission instead")

    def test_runtime_shape_is_scoped_to_the_conjunction_case(self):
        """The run-time shape must not read as licence for symptom tracing.

        Read alone, "the line at which the defect surfaces at run time even
        though that line is correct in isolation" is satisfied by almost any
        downstream crash site for an ordinary single-cause bug — any
        intermediate call site is "correct in isolation" and is somewhere
        the defect "surfaces at run time". The clause is only valid for a
        defect that is the conjunction of two lines, neither wrong alone
        (the pg-pool manifest/import case); pinning that scoping phrase next
        to "run time" on both always-read surfaces stops a future edit from
        widening the shape back into general symptom-anchoring licence.
        """
        for path in (SKILL_MD, HARNESS_REVIEW_BODY):
            with self.subTest(path=path):
                self.assertRegex(
                    _read(path), _RUNTIME_SHAPE_SCOPE_PATTERN,
                    f"{path} must tie the run-time further-location shape "
                    "to a defect that is the conjunction of two lines, "
                    "neither wrong alone — not state it as an unscoped "
                    "licence to anchor at any correct-in-isolation site")


class ImpactInstancesPresentTest(unittest.TestCase):
    """All three rubric surfaces name the three concrete impact instances.

    The abstract impact rule (data loss, corruption, exposure, a broken
    guarantee) is four nouns a reviewer did not recognise in practice: on
    v0.6.261 `QuerySummaries` stayed `low` in all three rounds while its own
    finding text described a 200 with an empty page, a non-zero total, and
    `has_more` true — it never connected that to "a broken guarantee". Each
    instance here is drawn from a measured defect (`QuerySummaries`,
    `cleanup_media`, `move_file`), so the test asserts on a distinctive
    phrase per instance rather than a whole sentence — a later reword of the
    surrounding prose should not break this test spuriously.
    """

    def test_each_instance_appears_on_every_surface(self):
        for path in (SKILL_MD, HARNESS_REVIEW_BODY, COPILOT_SKILL_MD):
            text = _read(path)
            for pattern in IMPACT_INSTANCE_PATTERNS:
                with self.subTest(path=path, pattern=pattern.pattern):
                    self.assertRegex(
                        text, pattern,
                        f"{path} is missing a concrete impact instance "
                        f"matching {pattern.pattern!r}")


class NoDropRuleTest(unittest.TestCase):
    """All three rubric surfaces state the no-drop rule.

    Measured on v0.6.261 (3 PRs x 3 rounds): edge-case findings fell from
    4/3/1 to 1/1/0 per round, 8 total down to 2, while test-coverage findings
    stayed exactly flat at 4/4/4. The `low` bullet's "nothing lost, corrupted,
    exposed, or promised and unmet" definition left those findings with
    neither a kind to anchor on nor a severity they could prove, so the
    reviewer reported nothing rather than rate them. That is a worse failure
    mode than mis-rating: a mis-rated defect is at least countable. Because
    the `medium` rubric already names "an unhandled edge case", a re-rating
    would have moved these findings *up*, not away, which is the evidence
    they were being dropped rather than re-rated. This pins the fix: never
    omit a finding for an unclear severity, report the best estimate instead.
    """

    def test_all_rubric_surfaces_state_the_no_drop_rule(self):
        for path in (SKILL_MD, HARNESS_REVIEW_BODY, COPILOT_SKILL_MD):
            with self.subTest(path=path):
                self.assertRegex(
                    _read(path), _NO_DROP_RULE_PATTERN,
                    f"{path} must state that an unclear severity is never "
                    "grounds to drop a finding, and that the finding is "
                    "instead reported at a best estimate, flagged uncertain")


class ImpactFloorParityTest(unittest.TestCase):
    """All three rubric surfaces carrying the low bullet also carry the
    rating rule beside it.

    The low bullet names no kind of defect any more — the kinds moved to the
    breadth sweep — so without a stated rule that severity follows impact
    rather than kind, a data-loss bug that arrives as a swallowed error could
    still be rated `low`, and low never blocks a merge. A benchmarking run
    found exactly that: a file lost when `chmod` failed after a rename, rated
    low.

    The copilot template used to be excluded here: it carried the older
    style-and-nits rubric, a tracked inconsistency rather than a surface this
    rule applied to. That rubric is now fixed to match the other two, so the
    template joins the loop — the widened parity check is what stops the
    drift recurring.
    """

    def test_all_rubric_surfaces_state_the_rating_rule(self):
        for path in (SKILL_MD, HARNESS_REVIEW_BODY, COPILOT_SKILL_MD):
            with self.subTest(path=path):
                self.assertTrue(
                    _impact_floor_stated(_read(path)),
                    f"{path} must state that severity follows what the "
                    "defect does rather than the kind of defect it is, and "
                    "that impact (data loss, corruption, exposure, a broken "
                    "guarantee) rates a finding medium or high")

    def test_pr_description_reference_drops_the_retired_floor_name(self):
        """`pr-description.md` names the rubric by reference, not by rubric
        text of its own — but it used to name the retired "impact floor"
        bullet by its old name. A semantic review of this change (PR 271)
        found that stale reference still pointing at a bullet this change
        renamed to "Impact rule" everywhere else, a dangling cross-reference
        on a file loaded on nearly every PR review. This pins the rename.
        """
        path = os.path.join(REFERENCES_DIR, "pr-description.md")
        text = _read(path).lower()
        self.assertNotIn(
            "impact floor", text,
            f"{path} still names the retired 'impact floor' bullet; it was "
            "renamed to 'impact rule' on every rubric surface")


class LowBulletNamesNoKindTest(unittest.TestCase):
    """The `low` bullet itself names no defect kind, on any of the three
    rubric surfaces.

    Measured on a ReviewBench benchmark run (v0.6.260, 3 rounds): printing
    the defect kinds under the `low` heading is what made the impact floor
    lose every time it mattered — `move_file` deleting the only copy, rated
    `low` in one round and `medium` in another, and `QuerySummaries`
    swallowing a database error, rated `low` in all three rounds. The kinds
    now live in the breadth-sweep step, where they are a detection aid
    rather than a severity label; this test pins the other half of that
    move — that the `low` bullet never lists them again.
    """

    def test_low_bullet_names_no_moved_defect_kind(self):
        for path in (SKILL_MD, HARNESS_REVIEW_BODY, COPILOT_SKILL_MD):
            with self.subTest(path=path):
                bullet = _low_bullet_text(_read(path)).lower()
                found = [w for w in MOVED_KIND_WORDS if w in bullet]
                self.assertFalse(
                    found,
                    f"{path}'s low bullet still names defect kind(s) "
                    f"{found}: {bullet!r}")

    def test_copilot_low_bullet_drops_the_style_and_nits_wording(self):
        bullet = _low_bullet_text(_read(COPILOT_SKILL_MD)).lower()
        for phrase in ("redundancy", "defensive nits"):
            self.assertNotIn(
                phrase, bullet,
                f"copilot template's low bullet still carries {phrase!r}, "
                "the contradiction task 5.1 was meant to remove")


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

    def test_value_set_contains_all_eleven_values(self):
        missing = ALL_TAXONOMY_VALUES - self.json_values
        self.assertFalse(
            missing,
            f"{JSON_OUTPUT_MD} taxonomy is missing values: "
            f"{sorted(missing)}")


class BaseFreshnessParityTest(unittest.TestCase):
    """The fetch-before-every-mode rule is stated on both surfaces that run
    outside `${CLAUDE_PLUGIN_ROOT}` resolution: the skill's own `SKILL.md`
    and the harness command body, which cannot read a file under
    `skills/review/references/`."""

    def test_both_surfaces_state_the_fetch_before_every_mode_rule(self):
        for path in (SKILL_MD, HARNESS_REVIEW_BODY):
            with self.subTest(path=path):
                text = _read(path)
                self.assertIn(
                    "every mode", text,
                    f"{path} does not state the fetch runs in every mode")
                self.assertIn(
                    "remote-tracking refs only", text,
                    f"{path} does not name the fetch's write scope")


class EndpointsFieldParityTest(unittest.TestCase):
    """The `endpoints` object is specified identically by both
    machine-payload surfaces: the plugin skill's `json-output.md` and the
    harness reference that ships to every harness declaring
    `file-references`."""

    FIELDS = ("base_given", "base", "base_sha", "head", "head_sha",
             "merge_base", "mode")

    def test_both_surfaces_name_the_same_endpoints_field_set(self):
        for path in (JSON_OUTPUT_MD, HARNESS_REVIEW_MD):
            with self.subTest(path=path):
                text = _read(path)
                for field in self.FIELDS:
                    self.assertIn(
                        f'"{field}"', text,
                        f"{path} does not name endpoints field {field!r}")


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


class ChangeFieldParityTest(unittest.TestCase):
    """The `change` object is specified identically by both
    machine-payload surfaces: the plugin skill's `json-output.md` and the
    harness reference that ships to every harness declaring
    `file-references`. It carries `slug`, `location`, and `dir`."""

    FIELDS = ("slug", "location", "dir")

    def test_both_surfaces_name_the_same_change_field_set(self):
        for path in (JSON_OUTPUT_MD, HARNESS_REVIEW_MD):
            with self.subTest(path=path):
                text = _read(path)
                self.assertIn(
                    '"change"', text,
                    f"{path} does not name a `change` member")
                for field in self.FIELDS:
                    self.assertIn(
                        f'"{field}"', text,
                        f"{path} does not name change field {field!r}")


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


HEREDOC_PY_RE = re.compile(r"<<'PY'\n(.*?)\n( *)PY\n", re.DOTALL)


def _extract_heredoc_python(yml_text):
    """The posting step's inline Python: the body of the one `<<'PY' ... PY`
    heredoc in `copilot-review-gate.yml`, dedented to real module-level
    Python source."""
    match = HEREDOC_PY_RE.search(yml_text)
    if not match:
        raise AssertionError(
            "expected a <<'PY' ... PY heredoc in copilot-review-gate.yml")
    body, indent = match.group(1), match.group(2)
    lines = []
    for line in body.split("\n"):
        if line.startswith(indent):
            lines.append(line[len(indent):])
        elif not line.strip():
            lines.append("")
        else:
            raise AssertionError(
                "heredoc line under-indented relative to its PY "
                "terminator: %r" % line)
    return "\n".join(lines)


def _workflow_namespace():
    """Executes the posting step's constants and function definitions in an
    isolated namespace, so a test reads `SEV_DOT`, `inline_body`, and
    `prose` from the real workflow source rather than a value hard-coded
    here that could silently drift from it.

    The source unpacks `sys.argv` at module scope before any function is
    defined, so `sys.argv` is stubbed for the exec; the module's tail (past
    the constants and function definitions) reads and writes real files
    named from those argv entries, which this test has no business
    touching, so the source is cut before that point.
    """
    source = _extract_heredoc_python(_read(COPILOT_GATE_YML))
    cutoff = source.index("with open(body_path")
    source = source[:cutoff]
    namespace = {}
    old_argv = sys.argv
    try:
        sys.argv = ["prog", "body", "findings", "files", "payload",
                    "fallback"]
        exec(compile(source, COPILOT_GATE_YML, "exec"), namespace)
    finally:
        sys.argv = old_argv
    return namespace


class FooterParityTest(unittest.TestCase):
    """Both posting surfaces close the posted body with the same stat line,
    counted from the pull request's own file list. The workflow's `footer`
    carries its own copy of the format, so it is pinned here against the real
    `review_gate.review_footer` rather than a restatement of it."""

    CASES = (
        [],
        ["junk"],
        [{"filename": "a.py"}],
        [{"filename": "a.py", "additions": 12, "deletions": 3}],
        [{"filename": "a.py", "additions": 12, "deletions": 3},
         {"filename": "b.py", "additions": 100, "deletions": 0},
         {"filename": "c.py", "patch": ""}],
        [{"filename": "a.py", "additions": True, "deletions": 3}],
    )

    @classmethod
    def setUpClass(cls):
        cls.workflow = _workflow_namespace()

    def test_workflow_footer_matches_review_gate(self):
        footer = self.workflow["footer"]
        for files in self.CASES:
            with self.subTest(files=files):
                expected = review_gate.review_footer(files)
                block = footer(files)
                if expected is None:
                    self.assertEqual(block, [])
                else:
                    self.assertEqual(block, ["", expected])

    def test_workflow_footer_ignores_a_non_list_diff(self):
        self.assertEqual(self.workflow["footer"](None), [])
        self.assertEqual(self.workflow["footer"]({"filename": "a.py"}), [])

    def test_folded_footer_keeps_the_verdict_marker_last(self):
        """The footer is folded above the verdict marker, so the gate's
        backwards marker scan still reads the marker from the body's last
        non-blank line, with the footer directly above it."""
        fold, footer = self.workflow["fold"], self.workflow["footer"]
        files = [{"filename": "a.py", "additions": 12, "deletions": 3}]
        for marker in self.workflow["MARKERS"]:
            with self.subTest(marker=marker):
                body = "## Findings: x\n\nsome text\n\n%s\n" % marker
                folded = fold(body, footer(files))
                lines = [ln for ln in folded.splitlines() if ln.strip()]
                self.assertEqual(lines[-1], marker)
                self.assertEqual(lines[-2], "Reviewed 1 file, +12 -3 lines.")
        bare = fold("no marker here\n", footer(files))
        self.assertEqual([ln for ln in bare.splitlines() if ln.strip()],
                         ["no marker here", "Reviewed 1 file, +12 -3 lines."])


class NoProblemsWordingTest(unittest.TestCase):
    """A clean review says "No problems found." on every surface that renders
    one — `review_gate.py`, the copilot reviewer's body instructions, and the
    review skill's own report rules — and the retired "No findings." wording
    appears on none of them."""

    SURFACES = (SKILL_MD, COPILOT_SKILL_MD)

    def test_review_gate_constant(self):
        self.assertEqual(review_gate.NO_PROBLEMS, "No problems found.")

    def test_prose_surfaces_carry_the_wording(self):
        for path in self.SURFACES:
            with self.subTest(path=os.path.basename(path)):
                text = _read(path)
                self.assertIn("No problems found.", text)
                self.assertNotIn("No findings.", text)

    def test_prose_surfaces_name_the_footer(self):
        for path in self.SURFACES:
            with self.subTest(path=os.path.basename(path)):
                self.assertIn("Reviewed N files, +A -D lines.", _read(path))


class FindingLocationSchemaTest(unittest.TestCase):
    """The `location` field becomes `locations`, an array of site strings.

    Both `json-output.md` and `harness/references/review.md` document a
    finding's location as a non-empty `locations` array, where `locations[0]`
    is the primary/fix site and any further entries are recurring sites.
    """

    def test_json_output_documents_locations_array(self):
        text = _read(JSON_OUTPUT_MD)
        # Check for the locations array in the example
        self.assertIn(
            '"locations":', text,
            f"{JSON_OUTPUT_MD} must document a `locations` array field")
        self.assertIn(
            '"locations": [', text,
            f"{JSON_OUTPUT_MD} must show `locations` as a non-empty array")
        # Check that the old singular location is not present
        self.assertNotIn(
            '"location": "path/to/file.ext:LINE"', text,
            f"{JSON_OUTPUT_MD} must not contain the singular `location` "
            "string field")

    def test_harness_reference_documents_locations_array(self):
        text = _read(HARNESS_REVIEW_MD)
        # Check for the locations array in the example
        self.assertIn(
            '"locations":', text,
            f"{HARNESS_REVIEW_MD} must document a `locations` array field")
        self.assertIn(
            '"locations": [', text,
            f"{HARNESS_REVIEW_MD} must show `locations` as a non-empty array")
        # Check that the old singular location is not present
        self.assertNotIn(
            '"location": "path/to/file.ext:LINE"', text,
            f"{HARNESS_REVIEW_MD} must not contain the singular `location` "
            "string field")

    def test_both_surfaces_document_locations_identically(self):
        json_text = _read(JSON_OUTPUT_MD)
        harness_text = _read(HARNESS_REVIEW_MD)
        # Both should mention locations as the primary/fix site
        for path, text in [
            (JSON_OUTPUT_MD, json_text),
            (HARNESS_REVIEW_MD, harness_text),
        ]:
            with self.subTest(path=path):
                self.assertIn(
                    "locations[0]", text,
                    f"{path} must state that locations[0] is the "
                    "primary/fix site")
                self.assertIn(
                    "non-empty", text,
                    f"{path} must state that locations is a non-empty array")


class SeverityDotParityTest(unittest.TestCase):
    """The `review-skill` requirement binds both posting surfaces —
    `review_gate.py` and the vendored `copilot-review-gate.yml` workflow —
    to render the identical severity dot, but each carries its own copy of
    the dot map and the marker format. Nothing failed if the workflow's copy
    drifted from `review_gate.py`'s until this test: it pins the workflow's
    rendering against the real `review_gate` module, not a second
    hard-coded restatement of it.
    """

    @classmethod
    def setUpClass(cls):
        cls.workflow = _workflow_namespace()

    def test_sev_dot_maps_are_identical(self):
        self.assertEqual(self.workflow["SEV_DOT"], review_gate._SEV_DOT)

    def test_inline_body_opens_with_review_gates_marker(self):
        inline_body = self.workflow["inline_body"]
        for sev in ("high", "medium", "low"):
            with self.subTest(severity=sev):
                body = inline_body({"severity": sev, "detail": "something"})
                expected_prefix = review_gate._sev_marker(sev)
                self.assertTrue(
                    body.startswith(expected_prefix),
                    "workflow inline_body for %r opens with %r, expected "
                    "the review_gate marker %r"
                    % (sev, body, expected_prefix))

    def test_folded_finding_bracket_matches_render_summary(self):
        prose = self.workflow["prose"]
        for sev in ("high", "medium", "low"):
            with self.subTest(severity=sev):
                block = prose([{"severity": sev, "detail": "something",
                                 "path": "z.py", "start_line": 1}])
                dot = review_gate._SEV_DOT[sev]
                expected_bracket = "[%s %s]" % (dot, sev)
                joined = "\n".join(block)
                self.assertIn(
                    expected_bracket, joined,
                    "workflow folded finding is missing %r: %r"
                    % (expected_bracket, joined))


# The `related` step's own heading, independent of its step number (which
# SkillMdStructureTest's renumbering tests pin elsewhere) — matches
# "### N. Pull related file context" wherever N lands after a renumber.
_RELATED_STEP_HEADING_RE = re.compile(
    r"^###\s+\d+\.\s*Pull[*_\s]+related[*_\s]+file[*_\s]*context[^\n]*\n"
    r"(.*?)(?=\n### |\Z)", re.DOTALL | re.MULTILINE)

# The checks the related-file context feeds — named identically (modulo
# whitespace/emphasis) on both surfaces that carry the step inline, so a
# reviewer handed files always has the reason to read them.
_RELATED_CHECKS_SERVED_PATTERN = re.compile(
    r"(?is)downstream-impact[*_\s]+and[*_\s]+call-site[*_\s]+checks")
_RELATED_LENSES_PATTERN = re.compile(
    r"(?is)lenses[*_\s]+that[*_\s]+compare[*_\s]+a[*_\s]+change[*_\s]+against"
    r"[*_\s]+unchanged[*_\s]+code")

# The limit stated beside the permission: a file `related` did not name
# stays unread, whatever else looks interesting — the engine's named set is
# what widens context, never the reviewer's own discretion.
_UNNAMED_FILE_UNREAD_PATTERN = re.compile(
    r"(?is)did[*_\s]+not[*_\s]+name[*_\s]+stays[*_\s]+unread")


class RelatedFileContextStepTest(unittest.TestCase):
    """Both reference-free surfaces — `SKILL.md` and the harness review
    body, neither of which can defer this always-applies guidance to a
    conditionally-loaded reference — carry the `related` step inline: the
    step itself, the checks it feeds, and the limit that a file the
    subcommand did not name stays unread.
    """

    def test_skill_md_names_the_related_step_section(self):
        match = _RELATED_STEP_HEADING_RE.search(_read(SKILL_MD))
        self.assertIsNotNone(
            match, "no 'Pull related file context' step heading found in "
            "SKILL.md")

    def test_both_surfaces_name_the_checks_it_serves(self):
        for path in (SKILL_MD, HARNESS_REVIEW_BODY):
            with self.subTest(path=path):
                text = _read(path)
                self.assertRegex(
                    text, _RELATED_CHECKS_SERVED_PATTERN,
                    f"{path} must name the downstream-impact and call-site "
                    "checks the related-file context feeds")
                self.assertRegex(
                    text, _RELATED_LENSES_PATTERN,
                    f"{path} must name the lenses that compare a change "
                    "against unchanged code")

    def test_both_surfaces_state_the_unnamed_file_stays_unread_limit(self):
        for path in (SKILL_MD, HARNESS_REVIEW_BODY):
            with self.subTest(path=path):
                self.assertRegex(
                    _read(path), _UNNAMED_FILE_UNREAD_PATTERN,
                    f"{path} must state that a file the related search did "
                    "not name stays unread")


if __name__ == "__main__":
    unittest.main()
