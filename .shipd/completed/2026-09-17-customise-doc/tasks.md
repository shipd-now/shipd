- [x] [req: customisation-guide] In `docs/customise.md`, add the reference
      page that inventories configuration, delivery stages, file-authored
      surfaces, harness selection, environment overrides, and current limits;
      link each detailed grammar authority instead of duplicating it.
- [x] [P1] [req: customisation-guide] In
      `plugins/s/skills/build/tests/test_config_sample.py`, add a drift test
      that fails with the names of recognized config keys missing from
      `docs/customise.md`.
- [x] [P1] [req: customisation-guide] In `README.md`,
      `docs/cheatsheet.md`, and `docs/getting-started.md`, add links to
      `docs/customise.md` without restructuring those pages.
- [x] [req: customisation-guide] Run the config-sample tests and
      `plugins/s/skills/document/scripts/docs_lint.py` over every touched
      documentation page; fix all failures and keep each page within its
      doc-type line cap.
