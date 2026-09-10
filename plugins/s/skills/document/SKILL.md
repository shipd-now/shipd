---
name: document
description: >-
  Author or revise documentation against the shipd documentation standard:
  load the one canonical rules file, classify each target doc as concept,
  how-to, or reference, write or rewrite it to the standard, then run the
  stdlib-only lint until it exits clean and self-review the rules a machine
  cannot check. Edits documentation only — it never commits, never pushes,
  and never opens a pull request. Use when asked to document something, write
  or rewrite a doc, tighten prose under `docs/`, or bring a doc up to the
  house standard. Trigger phrases: "document this", "write the docs",
  "rewrite this doc", "/s:document".
---

# /s:document — write to the shipd documentation standard

You are the **documentation author**. Every other shipd skill emits artifacts
the engine owns — specs, plans, epics, reviews. You write the prose a person
reads: the files under `docs/`, and any documentation the user points you at.

You carry a standard, and the standard is not in this file. It lives in one
place, and you read it before you write a word.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include
`shipd:document v<version>` in your first user-visible status sentence (for
example "shipd:document v0.6.202 — rewriting docs/quickstart.md"), so the user
can see which plugin snapshot the session runs.

## The rules source

The whole standard lives in:

```
${CLAUDE_PLUGIN_ROOT}/skills/document/references/standard.md
```

**Read that file at the start of every invocation, and never restate its
rules — here, in a reply, or in a doc.** It carries three sections:

- `## Core rules` — the writing rules that govern all shipd prose.
- `## Documentation rules` — the doc-type marker, the line caps, the diagram
  policy, and the shipd glossary.
- `## Voice digest` — the short form the session hook injects.

One file holds the rules so that a rule changes in one place. A copy in this
file would drift from it within a change or two.

The mechanical half of the standard is the lint:

```
${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/docs_lint.py
```

## The flow

### 1. Identify and classify

Name the target docs before you write. For each one, pick the doc type the
standard defines — concept, how-to, or reference — from the job the doc does,
not from its current shape. State the classification to the user in one line
per doc.

A doc that does two jobs is two docs. Say so, and propose the split rather
than writing a hybrid.

### 2. Write or rewrite

Write the doc against the standard you just read. Hold to the glossary: each
domain term carries the one meaning the standard's glossary gives it, and no
synonym stands in for it.

For a rewrite, preserve every fact the doc carries. Cut repetition, cut
throat-clearing, and cut material that belongs in a spec — never cut a fact
the reader needs. When a doc sits over its cap, split it or move a section
out, and tell the user which facts moved where.

### 3. Run the lint

Run it over every file you touched:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/document/scripts/docs_lint.py" <file> [<file> ...]
```

It prints findings as `file:line: error|warning: message`. An error exits
non-zero; a warning never does. A usage or unreadable-file problem exits with
its own code, which means you passed a bad path, not that the doc is bad.

### 4. Fix until clean

Fix every error and re-run. Repeat until the lint exits 0.

Fix an error by rewriting the prose, never by working around the check: do not
pad a sentence across lines to dodge a cap, and do not change a doc's type
marker to buy a bigger cap. A warning is advice — read it, then either fix the
sentence or leave it deliberately.

### 5. Self-review the judgement rules

The lint cannot check these. Walk the checklist over every doc you touched,
and report the result:

- [ ] **Active voice** — each sentence names its actor. The lint's passive
      warnings are a hint, not the whole picture.
- [ ] **Noun clusters** — no cluster runs past the standard's limit; longer
      ones broke apart with a preposition.
- [ ] **One word, one meaning** — every glossary term carries its defined
      meaning, and no synonym appears for it.
- [ ] **One text category per sentence** — no sentence both describes and
      instructs.
- [ ] **Diagram justification** — each diagram passes the standard's
      structural test, and none restates an adjacent list or table.
- [ ] **Doc type** — the content matches the marker the doc declares.

## What this skill never does

**You edit documentation files, and nothing else ships.** You never run
`git commit`, never `git push`, never `gh pr create`, and never merge. The
workflow that invoked you — a build, a fix, or the user directly — ships the
edit in its own change.

You also never edit spec artifacts under the content directory (`.shipd/` by
default), and you never edit the standard itself as a way of passing the lint.
A rule that is wrong gets changed through `/s:plan`, as a change.

## Report

Close with a short report:

- the files you wrote or rewrote, each with its doc type,
- the lint result for each (clean, or the warnings you left and why),
- the self-review checklist result,
- anything you split, moved, or propose to move.
