## 1. Poster: counted findings, folded lows, already-there section

- [x] 1.1 [req: gate-verdict-from-severity] In
      `plugins/s/skills/review/tests/test_review_gate.py`, change
      `PostDispositionTest.test_omitted_scope_defaults_to_all` to assert
      status `success` (keep its two `assertNotIn` checks). Add a
      `CountedFindingsTest` class using `FakeGh(files=[{"filename": "a.py",
      "patch": PATCH_A}])`, `_review`, and an `out` collector list, with one
      test per `gate-verdict-from-severity` scenario. The cases:
      - low-only `changes-requested`: `success`, `result["review_event"] ==
        "APPROVE"`, `## Findings: ✅ Ship it`, one `verdict reconciled:` line.
      - `pass` with a `medium` at a changed `a.py` line: `failure` and
        `REQUEST_CHANGES`.
      - a `high` `security` finding at `install.sh:12` (not in the
        files): `success`, `APPROVE`, summary contains `### Already there,
        reached by this change` and the row suffix `(already there)`, and
        the finding is absent from `### Additional findings`.
      - a `medium` `bug` finding at an `a.py` line outside `PATCH_A`'s hunk:
        `success`.
      - a `medium` `bug` finding on a `PATCH_A` context line: `failure`.
      - a `high` `untouched-caller` finding at `install.sh:12`:
        `failure`.
      - a `high` `bug` finding with location `install.sh`: `failure`.
      - unmet `spec_coverage` with no findings: `failure`.
      - severity `critical`: `failure`.
      - `pass` with one `low`: `success`, no reconciliation line.
      - status description contains `1 already there` for the untouched-file
        case.

      Read `PATCH_A` and `commentable_lines` to pick the line numbers. Run
      `cd plugins/s/skills/review/tests && python3 -B -m unittest test_review_gate`
      and observe the new tests fail.
- [x] 1.2 [req: gate-poster] In the same test file, add a test that a `low`
      finding at a changed `a.py` line produces no inline comment and appears
      under `### Additional findings` with `🟡`. Change the `f2` finding in
      `test_submission_body_carries_the_speaker_heading` from `low` to
      `medium`, so its "2 inline comments" assertion still holds. Run the
      module and observe the new test fail.
- [x] 1.3 [req: folded-findings-disposition] In the same file, add a test
      that a `post` of a low-only review submits a review with no inline
      comments, then `resolve` over the resulting `FakeGh` reports zero
      unresolved. Add a test that `autoreply --disposition high-only` still
      replies to a pre-existing low thread given through
      `FakeGh(review_threads=...)` (copy the shape the existing autoreply
      tests use). Run and note which fail.
- [x] 1.4 [req: gate-verdict-from-severity] In
      `plugins/s/skills/review/scripts/review_gate.py`, add
      `BLOCKING_SEVERITIES = ("high", "medium")` below `DISPOSITIONS` with a
      comment naming it the single owner, and
      `EXEMPT_CATEGORIES = ("untouched-caller", "spec-coverage")` beside it.
- [x] 1.5 [req: gate-verdict-from-severity] In the same file, above
      `status_state`, add:
      - `_touched(path, line, files_by_name, commentable)`. It is True when
        `path in files_by_name` and either that file's `patch` is empty or
        missing, or `line in commentable[path]`.
      - `already_there(f, files_by_name, commentable)`. It is True when
        `f.get("category")` is a non-empty string not in
        `EXEMPT_CATEGORIES`, `_parse_locations(f)` is non-empty with every
        entry's path and line not `None`, and no location is `_touched`.
      - `effective_verdict(counted, spec_coverage)`. It returns
        `"changes-requested"` when any `f.get("severity", "low")` is in
        `BLOCKING_SEVERITIES` or not in `("high", "medium", "low")`, or any
        `(spec_coverage or [])` entry has `state == "unmet"`, else `"pass"`.

      Give each a docstring.
- [x] 1.6 [req: gate-verdict-from-severity, gate-poster] In `post()`,
      replace the block from `findings = review.get("findings") or []`
      through `state = status_state(...)`:
      - Build `files_by_name = {f.get("filename"): f for f in files}`.
      - Mark findings with `dict(f, already_there=True)` where
        `already_there(...)` holds.
      - `counted` = the unmarked findings.
      - `effective = effective_verdict(counted, review.get("spec_coverage"))`.
      - On a mismatch with `review.get("verdict")`, call
        `out("verdict reconciled: payload said %s, findings say %s" % (...))`.
      - Rebind `review = dict(review, verdict=effective, findings=marked)`.
      - `threadable = [f for f in counted if f.get("severity", "low") in BLOCKING_SEVERITIES]`.
      - `anchored, unanchored = _split_findings(threadable, commentable)`.
      - Append every counted non-threadable finding to `unanchored`.
      - `state = status_state(effective, counted, disposition)`.

      Leave `status_state` itself unchanged.
- [x] 1.7 [req: gate-verdict-from-severity] In `render_summary`:
      - Append ` (already there)` to the table detail cell of any finding
        with `already_there`.
      - Drop such findings from the `unanchored` loop.
      - After the "Additional findings" block, render `### Already there,
        reached by this change`, then the line `_Code this pull request did
        not change, reached by it. These never request changes._`, then one
        bullet per already-there finding in the same format as the
        additional-findings bullets.

      In `_status_description`, count only findings without
      `already_there`, and append `, N already there` when N > 0, before the
      suffix. Rerun the module; tasks 1.1–1.3 now pass.

## 2. CI gate classifies the findings file

- [x] 2.1 [req: gate-nonblocking-fix-required-greens] In
      `plugins/s/skills/review/tests/test_review_gate.py`, extend `_classify`
      with optional `findings=None` and `files=None`. When given, they are
      written as JSON to `<tempdir>/shipd-copilot-review-findings.json` and
      `<tempdir>/files.json`. The wrapper always prepends:
      - `RUNNER_TEMP=<tempdir>`
      - `py_bin=<sys.executable>`
      - `files_file=<tempdir>/files.json` (created empty when `files` is
        None)
      - `ungrounded=`

      Return the parsed `shipd-gate-finding-classes.json` as a third value
      (`None` when absent) and update existing callers. Add a test class with
      one test per `gate-nonblocking-fix-required-greens` scenario,
      fail_open `"false"`. The docs-only case uses `files=[{"filename":
      "docs/e2e.md", "patch": "@@ -0,0 +1,2 @@\n+a\n+b"}]` and a finding
      `{"severity": "high", "category": "security", "path":
      "install.sh", "start_line": 12, "end_line": 14, "detail": "d"}`.
      Run the module and observe the new tests fail.
- [x] 2.2 [req: gate-nonblocking-fix-required-greens] In
      `plugins/s/integrations/copilot/copilot-review-gate.yml`, classify step,
      directly before `if [[ -n "$state" ]]; then`, at 10-space indent:
      - When `${ungrounded:-}` is empty and `matched_state` is non-empty,
        write `$body` with `printf '%s'` to
        `${RUNNER_TEMP:-.}/shipd-gate-verdict-body.md`.
      - Run `"$py_bin" - <findings> "$files_file" <body> <classes-out>
        "$matched_state" <<'PY' ... PY`, where `<classes-out>` is
        `${RUNNER_TEMP:-.}/shipd-gate-finding-classes.json`.
      - The script builds `diff` with the same `commentable()` as the posting
        heredoc. It marks entry `i` already there per the requirement and
        writes `{"already_there": [...], "reclassified": <bool>}`.
        `reclassified` is true only when `matched_state` is `failure` and
        the downgrade condition holds; the script exits 0 iff it is true,
        and exits 1 on any exception, writing nothing.
      - On exit 0, set `matched_state=success`, `state=success`,
        `description="Copilot code review: ship it (only low or already-there findings)."`.

      Precede the block with a comment giving the rule and why it only
      downgrades.
- [x] 2.3 [req: gate-nonblocking-fix-required-greens] In the posting heredoc
      of the same file:
      - Read `${RUNNER_TEMP:-.}/shipd-gate-finding-classes.json` with `load()`
        (default `{}`), passed as a new seventh argv path.
      - Route entries whose index is in `already_there` to a new
        `already(findings)` prose block titled `### Already there, reached
        by this change`, formatted like `prose()`, never to `unverified` or
        `comments`.
      - When `reclassified` is true, insert `**Gate note:** the reviewer's
        fix-required verdict does not block: every finding is low or already
        there, reached by this change.` and a blank line directly after the
        brand line.

      Add a posting-payload test beside the existing ones for both. Rerun;
      2.1 and these pass.
- [x] 2.4 [req: gate-nonblocking-fix-required-greens] In
      `plugins/s/integrations/copilot/SKILL.md`:
      - Add a `category` bullet to the findings-file field list, with the
        `/s:review --json` category values and `untouched-caller` named for
        a caller the change left broken.
      - Add to the verdict rule that a finding located only in code the PR
        did not change, other than an untouched caller or unmet scenario, is
        reported as already there and never blocks.
      - Replace "So the file never decides what the review says — the body
        remains the review, and the verdict marker below is what gates the
        merge." with wording that keeps the marker as the gate except the
        exception this requirement defines.

## 3. Contracts, docs, version, verification

- [x] 3.1 [req: low-findings-docs-version] In
      `plugins/s/skills/review/references/posting.md`:
      - Change both `all`-scope descriptions ("`success` iff the verdict is
        `pass`") to the counted-findings rule and the `verdict reconciled:`
        line.
      - In step 5, say `low` findings fold into the summary and already-there
        findings get their own section.
      - In the disposition steps, say the loop acts on threaded findings
        only, and folded findings need no reply.
- [x] 3.2 [req: low-findings-docs-version] In
      `plugins/s/skills/review/references/json-output.md`, extend the
      "Rules:" paragraph: a finding whose every location is outside the diff
      hunks, and whose category is not `untouched-caller` or
      `spec-coverage`, does not count toward `verdict`; `review_gate.py post`
      recomputes `verdict` this way. In `plugins/s/skills/review/SKILL.md`,
      add the same exception to the "Any high **or** medium finding blocks"
      sentence and to the Findings-header rule.
- [x] 3.3 [req: low-findings-docs-version] Update
      `docs/semantic-review-reference.md` and
      `docs/copilot-review-reference.md` wherever they describe the status
      mapping, the marker-to-status mapping, or inline-vs-folded findings;
      find sites with
      `grep -n "fix-required\|iff the verdict\|inline" docs/semantic-review-reference.md docs/copilot-review-reference.md`.
- [x] 3.4 [req: low-findings-docs-version] In
      `plugins/s/.claude-plugin/plugin.json`, set `version` one patch above
      `git show origin/main:plugins/s/.claude-plugin/plugin.json`.
- [x] 3.5 [req: *] Run
      `cd plugins/s/skills/review/tests && python3 -B -m unittest discover`
      and `python3 -B -m unittest discover -s plugins/s/skills/build/tests`
      from the worktree root, grepping each output for `OK` or `FAILED`.
      Fix any test pinning the gate workflow text, the poster's inline
      behaviour, or the plugin version until both report `OK`.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 90 | 47.4k |
| SubagentHandback | 4 | 5.4k |
| SendMessage | 2 | 1.7k |
| (no tool) | 0 | 1.0k |
| Agent | 2 | 919 |
| Monitor | 1 | 76 |
| **Total** | 99 | 56.5k |
