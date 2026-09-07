#!/usr/bin/env python3
"""Drift guard for the copyable config example
(``plugins/s/skills/build/references/shipd.config.example.json``): it stays
strict JSON, documents exactly the keys ``spec_common.RECOGNIZED_CONFIG_KEYS``
registers, and declares nothing that differs from the engine's built-in
defaults (shipd-config config-sample-coverage)."""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "scripts"))
REFERENCE = os.path.normpath(os.path.join(
    HERE, "..", "references", "shipd.config.example.json"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import build_report as br  # noqa: E402
import spec_common as sc  # noqa: E402


def load_sample():
    """Parse the reference with the stdlib parser — no comment stripping, no
    tolerant mode: the file is copyable verbatim, so it must be strict JSON."""
    with open(REFERENCE) as fh:
        return json.load(fh)


def strip_comments(obj):
    """Drop every comment entry — the bare ``"//"`` header and each
    ``"// <key>"`` documentation entry — from a mapping, recursively, leaving
    only the keys the file actually declares."""
    declared = {}
    for key, value in obj.items():
        if key == "//" or key.startswith("// "):
            continue
        declared[key] = (
            strip_comments(value) if isinstance(value, dict) else value)
    return declared


def documented_keys(sample):
    """The top-level keys the sample documents: every declared key, plus the
    ``<key>`` named by each ``"// <key>"`` comment entry. The bare ``"//"``
    header entry documents no key and is excluded."""
    keys = set()
    for key in sample:
        if key == "//":
            continue
        if key.startswith("// "):
            keys.add(key[len("// "):].strip())
        else:
            keys.add(key)
    return keys


class TestConfigSample(unittest.TestCase):
    def test_sample_is_strict_json_object(self):
        """Scenario: The sample stays strict JSON."""
        sample = load_sample()
        self.assertIsInstance(sample, dict)

    def test_every_registry_key_is_documented(self):
        """Scenario: Every recognized key is documented."""
        documented = documented_keys(load_sample())
        missing = sorted(set(sc.RECOGNIZED_CONFIG_KEYS) - documented)
        self.assertEqual(
            missing, [],
            "recognized keys absent from the config example: %s" % missing)

    def test_no_unrecognized_key_is_documented(self):
        """Scenario: No unrecognized key is documented."""
        documented = documented_keys(load_sample())
        extra = sorted(documented - set(sc.RECOGNIZED_CONFIG_KEYS))
        self.assertEqual(
            extra, [],
            "config example documents unregistered top-level keys: %s" % extra)

    def test_key_constants_stay_in_the_registry(self):
        """Scenario: Key constants stay in the registry."""
        registry = set(sc.RECOGNIZED_CONFIG_KEYS)
        checked = []
        for name in dir(sc):
            if not name.endswith("_KEY"):
                continue
            value = getattr(sc, name)
            if not isinstance(value, str):
                continue
            checked.append(name)
            self.assertIn(
                value, registry,
                "%s = %r is not a member of RECOGNIZED_CONFIG_KEYS"
                % (name, value))
        self.assertTrue(checked, "no *_KEY constants found in spec_common")

    def test_declared_values_equal_the_built_in_defaults(self):
        """Scenario: Copying the sample changes no behavior."""
        declared = strip_comments(load_sample())
        self.assertEqual(sorted(declared), ["build"],
                         "unexpected declared keys: %s" % sorted(declared))
        self.assertEqual(declared["build"], br.DEFAULT_BUILD_CONFIG)


if __name__ == "__main__":
    unittest.main()
