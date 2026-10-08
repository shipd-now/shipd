## 1. Bring the branch current and raise the ceiling

- [x] 1.1 [req: *] Run `git fetch origin main && git merge origin/main`. This
      change edits `plugins/s/skills/review/SKILL.md` in the same region as
      v0.6.263, so reconcile before implementing rather than after. Report
      whether the merge was clean and what the file's line count is afterwards.
- [x] 1.2 [req: review-skill-references] Raise `test_under_line_ceiling` in
      `plugins/s/skills/review/tests/test_skill_references.py` from 350 to 370,
      and extend its docstring: the new step is guidance that runs on every
      review and so cannot be deferred to a reference, and the file sat at 340
      of 350 before this change. Do not restate 370 anywhere else — the
      `review-skill-references` requirement owns the figure and says so.

## 2. Build the related subcommand

- [x] 2.1 [req: related-context] In
      `plugins/s/skills/review/scripts/semdiff.py`, add a `cmd_related` and its
      `related` subparser taking `<base>`, an optional `<head>`, and
      `--mode balanced|max` defaulting to `balanced`. Resolve the changed-file
      list the same way `cmd_files` does, so `related` and `files` never
      disagree about what changed.
- [x] 2.2 [req: related-context] Find **importers** by searching for each
      changed file's module name — its basename without extension, and its
      extensionless repository path for languages that import by path — reusing
      the ripgrep-then-`git grep` ladder `cmd_context` already implements at
      `plugins/s/skills/review/scripts/semdiff.py`. Exclude the changed file
      itself from its own importer list.
- [x] 2.3 [req: related-context] Find **importees** by scanning each changed
      file's own import, require, use, and include lines and resolving the
      names against paths that exist in the repository. A name that resolves to
      nothing is dropped, not guessed at — a package from outside the
      repository is not a related file.
- [x] 2.4 [req: related-context] Apply the caps: 8 per changed file and 40 per
      review in `balanced`, 20 and 120 in `max`. Rank candidates by proximity —
      same directory first, then nearest common ancestor — so the cap keeps the
      likeliest files. Report every truncation as a count in the output. A
      silent truncation is the defect this task exists to prevent.
- [x] 2.5 [req: related-context] Emit the same best-effort note
      `semdiff context` emits, state the mode the run used, and fail the way
      `cmd_context` fails when neither `rg` nor `git` is present — naming the
      missing tools and exiting 127, rather than returning an empty set that
      reads like "no related files".
- [x] 2.6 [req: related-context] Add tests to
      `plugins/s/skills/review/tests/test_semdiff_files_context.py` covering:
      importers and importees both appearing; a per-file cap reporting its
      dropped count; `--mode max` raising both caps and naming the mode in the
      output; an unresolvable import name being dropped rather than guessed;
      and the changed file never appearing in its own importer list. Write the
      fixtures the test needs rather than extending a shared fixture whose file
      count another test asserts.

## 3. Teach the review to use it

- [x] 3.1 [req: review-skill] Add a workflow step to
      `plugins/s/skills/review/SKILL.md`, after the structural diff and before
      the judgement passes, that runs `related` and reads the files it names.
      The step must name which checks the context serves — the
      downstream-impact and call-site checks, and the lenses that compare a
      change against unchanged code — because a reviewer given files without a
      reason will read them and draw nothing from them.
- [x] 3.2 [req: review-skill] In the same step, state the limit as plainly as
      the permission: a file the subcommand did not name is still not read. The
      engine's set is what widens the skill's context economy, never the
      reviewer's own judgement about what might be interesting.
- [x] 3.3 [req: review-skill] Reconcile the skill's opening principle at the
      top of the same file, which currently reads that whole files are never
      read into context when the structural diff and targeted lookups will do.
      It must still rule out raw file dumps and model-chosen exploration while
      admitting the engine's named set. Change the sentence; do not delete it.
- [x] 3.4 [req: review-skill] Mirror the step and the limit in
      `plugins/s/harness/bodies/review.md`, which ships into other
      repositories, can read no reference file, and renumbers its steps when
      one is inserted. Check the renumbering: a two-digit marker needs
      four-space continuation indent, and a stale three-space indent has
      silently broken markdown here before.
- [x] 3.5 [req: review-skill] Add tests to
      `plugins/s/skills/review/tests/test_skill_references.py` pinning that
      both reference-free surfaces name the `related` step, the checks it
      serves, and the limit that an unnamed file stays unread. Guard the
      patterns against markdown emphasis with a character class such as
      `[*_\s]+`, and bound any heading-scoped regex with `[^\n]*\n` rather
      than `.*` under `re.DOTALL`.

## 4. Version and verification

- [x] 4.1 [req: *] Bump the `version` field in
      `plugins/s/.claude-plugin/plugin.json` to `0.6.264`.
- [x] 4.2 [req: *] Run `semdiff related` for real against this repository —
      `python3 plugins/s/skills/review/scripts/semdiff.py related HEAD~1` and
      the same with `--mode max` — and report the actual output: how many
      related files each mode names, whether any cap fired, and whether the
      importers it finds are genuinely importers. A subcommand that passes its
      unit tests and names useless files is a failure this task is meant to
      catch.
- [x] 4.3 [req: *] Run `python3 -m unittest discover -s
      plugins/s/skills/review/tests -v` and report the count against the
      246-test baseline that v0.6.263 leaves.
- [x] 4.4 [req: *] Run the build suite with stderr captured — `python3 -m
      unittest discover -s plugins/s/skills/build/tests > /tmp/bs264.log 2>&1;
      tail -4 /tmp/bs264.log` — because its summary goes to stderr and a
      stdout-only pipe loses the verdict silently. Report the verdict verbatim.
- [x] 4.5 [req: *] Run `python3
      plugins/s/skills/build/scripts/spec_lint.py` with no argument and then
      for this change by name; both must exit 0.
- [x] 4.6 [req: *] Report both ceilings as numbers: `plugins/s/skills/review/SKILL.md`
      against its new 370, and the rendered review harness body against 160.
- [x] 4.7 [req: review-skill] Add no reflow. Confirm with a word-level diff of
      `plugins/s/skills/review/SKILL.md` against the merge base that every word
      change falls inside the new step or the amended opening principle.
- [x] 4.8 [req: related-context] The importer search as built matches a bare
      occurrence of the file's name, so it reports documentation and spec
      artifacts that merely discuss a module as importing it. Measured against
      this repository: `semdiff.py`'s importers came back as `SKILL.md`,
      `json-output.md`, `linters.md` and `spec-aware.md`, with 136 candidates
      truncated away. Match the importing syntax of a language instead — the
      import, require, use or include form that names the module — and exclude
      non-source files from the candidate set entirely. A reviewer handed four
      markdown files and told they import the module is worse off than one
      handed nothing.
- [x] 4.9 [req: related-context] Importee detection returns nothing for
      `plugins/s/skills/review/scripts/semdiff.py`, which imports
      in-repository modules through its engine-import helper. Fix the
      resolution so an in-repository import is found, and keep dropping names
      that resolve to nothing outside the repository. Report the importees it
      finds for that file as evidence.
- [x] 4.10 [req: related-context] Re-run `python3
      plugins/s/skills/review/scripts/semdiff.py related HEAD~1` and the
      `--mode max` form after both fixes, and report for each non-empty entry
      whether every named importer genuinely imports the file. Judge the
      output, do not just confirm it parses: this subcommand's whole value is
      that the files it names are worth reading.
