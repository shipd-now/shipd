# Tasks

## 1. Lint: an unreferenced artefact is an error

- [x] 1.1 [P1] [req: artefact-reference-enforcement] In
      `plugins/s/skills/build/tests/test_spec_lint.py`, add failing tests over a
      temp change directory: (a) a change whose artefacts directory holds
      policy.md named nowhere in plan.md, tasks.md, or the delta lints with an
      error naming the change-relative artefact path; (b) the same change with
      plan.md naming that path lints clean; (c) a nested artefact one directory
      deep is matched by its full change-relative path; (d) a change with no
      artefacts directory keeps its current findings. Run them and observe them
      fail.
- [x] 1.2 [P2] [req: artefact-reference-enforcement] In
      `plugins/s/skills/build/scripts/spec_lint.py`, add
      `check_artefact_references(root, change, errors)`: return immediately
      unless the change's artefacts directory exists; build the haystack by
      concatenating plan.md, tasks.md, and every `specs/<capability>/spec.md`
      that exists; walk the artefacts tree with `os.walk` in sorted order and,
      for each file whose change-relative POSIX path is absent from the
      haystack, append a `LintError` naming that path. Call it from
      `lint_change` alongside the other change checks. Confirm task 1.1's tests
      pass.

## 2. Emit: staged artefacts install, orphans do not

- [x] 2.1 [P3] [req: per-change-artifact-layout, artefact-reference-enforcement] In
      `plugins/s/skills/build/tests/test_spec_emit.py`, add tests pinning the
      installed behavior: a staging directory whose artefacts directory holds
      policy.md, referenced from plan.md, installs with exit 0 and the file
      lands under the installed change directory; the same staging directory
      with the reference removed exits non-zero, prints the finding, and leaves
      no change directory behind. No engine edit is expected — `spec_emit.py`
      already copies the whole staging tree — so run the tests and confirm they
      pass as written.

## 3. Gate: change-relative artefact references resolve

- [x] 3.1 [P1] [req: artefact-reference-resolution] In
      `plugins/s/skills/build/tests/test_spec_gate.py`, add failing tests: a
      backticked change-relative artefact token in tasks.md whose file exists in
      the change directory produces no file-reference finding; the same token
      naming a file the change directory does not hold is still a finding; a
      mistyped repository path outside the artefacts prefix is still a finding.
      Run them and observe the first fail.
- [x] 3.2 [P2] [req: artefact-reference-resolution] In
      `plugins/s/skills/build/scripts/spec_gate.py`, extend `_check_task_paths`:
      after the root-relative `os.path.exists` test and before the
      parent/grandparent fallbacks, continue when the token begins with the
      artefacts prefix and resolves to an existing path inside
      `_planned_dir(root, change)`. Restrict the change-relative resolution to
      that prefix. Confirm task 3.1's tests pass.

## 4. Read verb: cat change lists artefacts

- [x] 4.1 [P1] [req: mediated-read-verb] In
      `plugins/s/skills/build/tests/test_spec_status.py`, add failing tests for
      `cat change`: a change whose artefacts directory holds one file prints,
      after the existing artifact output, a `--- artefacts` header and one line
      giving that file's root-relative path and byte size, without its content;
      two artefacts are listed sorted by path; a change with no artefacts
      directory prints no such header. Run them and observe them fail.
- [x] 4.2 [P2] [req: mediated-read-verb] In
      `plugins/s/skills/build/scripts/spec_status.py`, extend `cmd_cat`'s change
      branch: after `_cat_files`, walk the resolved change directory's artefacts
      tree; when it holds at least one file, print the `--- artefacts` header
      then one sorted line per file as its `os.path.relpath` against the
      invocation root followed by its `os.path.getsize` in bytes. Print no
      contents and leave the no-artefacts output byte-identical. Confirm task
      4.1's tests pass.

## 5. Conventions and handoff

- [x] 5.1 [P3] [req: per-change-artifact-layout] In `.shipd/README.md`, add the
      optional artefacts directory to the on-disk layout block under the change
      entry, and add a short subsection after "The plan document" stating what
      it holds, that every file must be referenced from plan.md, tasks.md, or a
      delta spec by its change-relative path, that the linter errors otherwise,
      and that the directory travels into the completed archive.
- [x] 5.2 [P3] [req: plan-artefact-storage] In
      `plugins/s/skills/plan/references/emission.md`, add the artefacts
      subdirectory to the staging layout block and a section after the delta
      specs' design-scratch subsection: stage standalone planning outputs there
      rather than pasting them into the artifacts, reference each from the
      artifacts that depend on it using its change-relative path, and stage
      nothing the change references nowhere since the emit refuses it.
- [x] 5.3 [P3] [req: artifact-compiled-context-handoff] In
      `plugins/s/skills/build/SKILL.md`, extend the handoff contract paragraph
      so the named artifact set includes the change's artefacts directory when
      present, read by its change-relative path and never pasted into the spawn
      message — mirroring the design-scratch sentence beside it.
- [x] 5.4 [P3] [req: artifact-compiled-context-handoff] In
      `plugins/s/agents/sub-agent.md` and `plugins/s/agents/validator.md`, add a
      presence-based bullet to each agent's read list: when the change carries
      an artefacts directory, read the artefacts its artifacts reference and
      treat their content as binding; where none is present the step is a no-op.
- [x] 5.5 [P3] [req: *] Bump the plugin version in
      `plugins/s/.claude-plugin/plugin.json` from 0.6.154 to 0.6.155.

## 6. Verification

- [x] 6.1 [req: *] Run the whole stdlib test suite under
      `plugins/s/skills/build/tests/` with system python3 and confirm it passes
      with no third-party packages installed.

## Token usage breakdown

| Tool | Calls | Output tokens |
| --- | --- | --- |
| Bash | 244 | 82.8k |
| Edit | 12 | 11.0k |
| Read | 30 | 8.7k |
| (no tool) | 0 | 7.5k |
| Agent | 4 | 988 |
| ToolSearch | 2 | 830 |
| SendMessage | 2 | 688 |
| **Total** | 294 | 112.5k |
