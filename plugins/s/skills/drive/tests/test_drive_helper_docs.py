#!/usr/bin/env python3
r"""Doc-drift test for `references/recording.md` against `record_worker.py`'s
`Helper` (drive-helper-docs): parses the bolded `h.<name>` entries the
reference documents in its "The helper API" section and asserts, via
`inspect.signature`, that each documented name resolves on `Helper`, that
each documented parameter name exists on that method, and that the
documented parameters appear in the order the real signature declares — so
a helper method renamed, re-signatured, re-ordered, or invented outright in
the reference fails this test by naming the mismatch, rather than silently
drifting.

Two entry shapes are parsed, both only as bolded list-item definitions
anchored to the start of a line:

- `` - **`h.method(args)`** `` — a method, checked for name, parameter
  names, and parameter order.
- `` - **`h.name`** `` — a parenthesis-free member, checked only for
  resolving on `Helper` as a method or an attribute. Without this shape a
  documented-but-nonexistent member (`h.cursor`) would slip past the suite
  entirely, since it never looks like a call.

The line anchor is what keeps the inline `` `h.hold(...)` ``/
`` `h.annotate(...)` `` cross-references in the prose and in "## The reveal
rule" out of the parsed set — those are illustrative, use a literal `...`
placeholder rather than real parameter names, and never appear as a bolded
list-item header. `test_the_parse_matches_only_real_api_entries` guards
that boundary directly, so a future widening of the pattern that starts
swallowing prose fails loudly instead of quietly weakening every assertion
below it.

`record_worker.py` declares `playwright` only as a `uv run` script
dependency (its `# /// script` header) and never imports it at module
scope — only inside `run_recording()` — but this suite still stubs a fake
`playwright`/`playwright.sync_api` module in `sys.modules` before importing
it, so the suite keeps needing no Playwright installed even if a future
edit moves that import to module scope.
"""

import importlib.util
import inspect
import os
import re
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
RECORD_WORKER_PATH = os.path.join(SCRIPTS, "record_worker.py")
RECORDING_DOC_PATH = os.path.normpath(
    os.path.join(HERE, "..", "references", "recording.md"))

# Only a bolded list-item header defines an API entry — e.g.
# "- **`h.glide_click(selector, steps=24)`** — glides the injected cursor
# ...", or the parenthesis-free "- **`h.cursor`** — ...". The argument
# list is optional so a documented plain member is parsed too. Anchored to
# the start of a line so the inline "`h.hold(...)`"/"`h.annotate(...)`"
# cross-references inside the reveal-rule prose (a literal `...`
# placeholder, never a real parameter list) are never matched.
_ENTRY_RE = re.compile(
    r"^- \*\*`h\.(\w+)(?:\(([^)]*)\))?`\*\*", re.MULTILINE)

# `self.<name> = ...` assignments inside `Helper`, so a documented plain
# member set up in `__init__` counts as defined even though it never lands
# on the class object itself. The `(?!=)` lookahead keeps a comparison
# (`self.foo == bar`) from reading as a definition, which would let a
# documented-but-nonexistent member resolve — the very drift this file
# exists to catch.
_SELF_ASSIGN_RE = re.compile(
    r"^\s*self\.(\w+)\s*(?::[^=]+)?=(?!=)", re.MULTILINE)


def _stub_playwright():
    """Install a minimal fake `playwright`/`playwright.sync_api` module
    into `sys.modules`, so importing `record_worker` needs no real
    Playwright installed."""
    if "playwright.sync_api" in sys.modules:
        return
    playwright_pkg = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = lambda *a, **kw: None
    playwright_pkg.sync_api = sync_api
    sys.modules.setdefault("playwright", playwright_pkg)
    sys.modules["playwright.sync_api"] = sync_api


def _load_record_worker():
    _stub_playwright()
    spec = importlib.util.spec_from_file_location(
        "drive_test_record_worker", RECORD_WORKER_PATH)
    module = importlib.util.module_from_spec(spec)
    # Registered before it executes so `inspect.getsource` can find the
    # class bodies it defines — without the entry, `inspect` resolves
    # `Helper.__module__` to nothing and calls it a built-in class.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _parse_documented_entries(doc_text):
    """Every bolded `h.<name>` entry `doc_text` documents, as a list of
    `(name, params)`, where `params` is the list of documented parameter
    names in documented order (any `=default` stripped) for an entry
    written as a call, and `None` for a parenthesis-free member."""
    entries = []
    for match in _ENTRY_RE.finditer(doc_text):
        name = match.group(1)
        raw_params = match.group(2)
        if raw_params is None:
            entries.append((name, None))
            continue
        params = []
        for part in raw_params.split(","):
            part = part.strip()
            if not part:
                continue
            params.append(part.split("=", 1)[0].strip())
        entries.append((name, params))
    return entries


def _helper_member_names(helper_cls):
    """Every name `Helper` defines — class-level methods and attributes,
    plus the instance attributes its own body assigns to `self`."""
    names = {
        name for name in vars(helper_cls)
        if not (name.startswith("__") and name.endswith("__"))
    }
    names.update(_SELF_ASSIGN_RE.findall(inspect.getsource(helper_cls)))
    return names


def _is_ordered_subsequence(documented, real):
    """True when `documented` appears inside `real` in that relative
    order (gaps allowed, so a doc may omit a parameter but never reorder
    the ones it names)."""
    it = iter(real)
    return all(name in it for name in documented)


class HelperDocMatchesImplementationTest(unittest.TestCase):
    def setUp(self):
        with open(RECORDING_DOC_PATH, encoding="utf-8") as fh:
            self.doc_text = fh.read()
        self.record_worker = _load_record_worker()
        self.entries = _parse_documented_entries(self.doc_text)

    def test_the_reference_documents_at_least_one_method(self):
        # Guards against the parser silently matching nothing and the rest
        # of this test class passing vacuously.
        self.assertTrue(
            [name for name, params in self.entries if params is not None])

    def test_the_parse_matches_only_real_api_entries(self):
        # The reference's prose cross-references helper methods inline as
        # `h.hold(...)` / `h.annotate(...)` with a literal `...`
        # placeholder. Those are illustrative, not API entries: if the
        # pattern ever widens to swallow them, `...` would parse as a
        # parameter name and every documented method would pick up a
        # duplicate, hollow entry. Both conditions below fail first.
        names = [name for name, _params in self.entries]
        self.assertEqual(
            sorted(names), sorted(set(names)),
            "recording.md parsed a duplicate h.<name> entry (%s) — the "
            "entry pattern is matching the prose cross-references, not "
            "just the bolded API list items" % (names,))
        for name, params in self.entries:
            for param_name in params or []:
                self.assertTrue(
                    param_name.isidentifier(),
                    "recording.md parsed %r as a parameter of h.%s — the "
                    "entry pattern is matching prose, not a real "
                    "signature" % (param_name, name))

    def test_every_documented_name_exists_on_helper(self):
        helper_cls = self.record_worker.Helper
        members = _helper_member_names(helper_cls)
        for name, params in self.entries:
            shape = "h.%s(...)" % name if params is not None else "h.%s" % name
            self.assertIn(
                name, members,
                "recording.md documents %s, which Helper defines neither "
                "as a method nor as an attribute" % shape)

    def test_every_documented_parameter_name_matches_the_signature(self):
        helper_cls = self.record_worker.Helper
        for name, params in self.entries:
            if params is None:
                continue  # a plain member, not a call
            method = getattr(helper_cls, name, None)
            if method is None:
                continue  # already reported by the previous test
            signature = inspect.signature(method)
            real_params = set(signature.parameters) - {"self"}
            for param_name in params:
                self.assertIn(
                    param_name, real_params,
                    "recording.md documents h.%s(..., %s, ...), which "
                    "Helper's real signature %s does not accept"
                    % (name, param_name, signature))

    def test_every_documented_parameter_order_matches_the_signature(self):
        helper_cls = self.record_worker.Helper
        for name, params in self.entries:
            if not params:
                continue  # a plain member, or a no-argument method
            method = getattr(helper_cls, name, None)
            if method is None:
                continue  # already reported by the name test
            signature = inspect.signature(method)
            real_params = [p for p in signature.parameters if p != "self"]
            if not set(params).issubset(set(real_params)):
                continue  # already reported by the parameter-name test
            self.assertTrue(
                _is_ordered_subsequence(params, real_params),
                "recording.md documents h.%s(%s), but Helper's real "
                "signature declares those parameters in the order %s"
                % (name, ", ".join(params), ", ".join(real_params)))


if __name__ == "__main__":
    unittest.main()
