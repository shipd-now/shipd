# codebase-first-unrun
Status: verified

## Idea

Keep the shared codebase-first rule from overriding the runnable-premise rule.

### Motivation

After #455 widened `Codebase first`, a harness plan eval run cited code as proof of current behaviour and never deferred an unrun premise. The `list-empty` case failed once in four runs.

### Details

- `Codebase first` says that reading code does not observe behaviour, so an unrun behaviour stays unrun under the readiness premise rule.

### Non-goals

- No change to the readiness rules or any other headless part.

## Implementation

- One sentence in `plugins/s/skills/ask/references/headless.md`, pinned by a test in `test_external_loaders.py`.

## Summary

Make the shared codebase-first rule defer unrun behaviour to the readiness premise rule.
