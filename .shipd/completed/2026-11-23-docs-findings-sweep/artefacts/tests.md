# Test additions — docs-findings-sweep

Add each block exactly as written, at the place its heading names. Indent as
shown: each method sits four spaces inside its class.

## `plugins/s/skills/build/tests/test_shipd_cli.py`

Add these two methods directly after the method
`test_the_banner_names_the_workspace_mode_words`, in the same class:

````python
    def test_the_banner_calls_harness_files_generated_command_files(self):
        r = self.cli("--help")
        self.assertEqual(r.returncode, 0)
        banner = " ".join(r.stdout.split())
        self.assertIn(
            "the harness registry, and the generated command files in a "
            "repo or in your home", banner)
        self.assertNotIn("generated /s:", banner)

    def test_the_docstring_serves_worktree_remove(self):
        with open(BIN, encoding="utf-8") as fh:
            source = " ".join(fh.read().split())
        self.assertNotIn("``autopilot``, ``worktree remove``) stay", source)
        self.assertIn("``worktree remove`` runs here", source)
        self.assertNotIn("generated ``/s:`` command files", source)
````

## `plugins/s/skills/build/tests/test_build_report.py`

Add these two methods to the class `BuildConfigTest`, directly after the
method `test_write_log_entry_creates_dir_on_demand`:

````python
    def test_the_report_never_creates_the_config_file(self):
        cfg = br.build_config(self.proj)
        br.write_log_entry({"change": "my-change", "status": "ok"}, cfg)
        self.assertFalse(
            os.path.exists(os.path.join(self.home, ".shipd-config.json")))
        self.assertFalse(
            os.path.exists(os.path.join(self.proj, ".shipd-config.json")))

    def test_the_build_skill_says_the_report_only_reads_the_config(self):
        with open(os.path.join(HERE, "..", "SKILL.md"),
                  encoding="utf-8") as fh:
            skill = fh.read()
        self.assertNotIn("on first run, creates", skill)
        self.assertIn("never creates it", skill)
````
