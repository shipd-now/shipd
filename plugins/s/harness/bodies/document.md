<!-- description: Author or revise documentation against the shipd documentation standard, then lint it clean — docs only, nothing shipped. -->
# /s:document — write to the shipd documentation standard

Write the prose a person reads — the files under `docs/`, and any
documentation the user points you at. The standard you write to is not in this
body: it lives in one canonical file, and you read it before you write a word.

<!-- include:preamble -->

The rules file and the lint sit beside the engine, under the same snapshot
`$S` resolves:

```sh
STD="$S/../../document/references/standard.md"
LINT="$S/../../document/scripts/docs_lint.py"
```

1. **Read the standard.** Read `$STD` in full at the start of every
   invocation. It carries `## Core rules` (the writing rules for all shipd
   prose), `## Documentation rules` (the doc-type marker, the line caps, the
   diagram policy, the shipd glossary), and `## Voice digest`. Never restate
   its rules — not here, not in a reply, not in a doc. One file holds them so
   that a rule changes in one place.
2. **Identify and classify.** Name the target docs, then pick each one's type
   — concept, how-to, or reference — from the job the doc does, not from its
   current shape. State the classification to the user in one line per doc. A
   doc that does two jobs is two docs: propose the split rather than writing a
   hybrid.
3. **Write or rewrite.** Write against the standard you just read, and hold to
   its glossary — each domain term carries its one defined meaning, and no
   synonym stands in for it. For a rewrite, preserve every fact the doc
   carries: cut repetition, throat-clearing, and material that belongs in a
   spec, never a fact the reader needs. When a doc sits over its cap, split it
   or move a section out, and say which facts moved where.
4. **Run the lint.** Run `python3 "$LINT" <file> [<file> ...]` over every file
   you touched. Findings print as `file:line: error|warning: message`. An
   error exits non-zero, a warning never does, and a usage or unreadable-file
   exit means you passed a bad path rather than a bad doc.
5. **Fix until clean.** Fix every error and re-run until the lint exits 0. Fix
   an error by rewriting the prose, never by working around the check: do not
   pad a sentence across lines to dodge a cap, and do not change a doc's type
   marker to buy a bigger cap. A warning is advice — fix the sentence, or
   leave it deliberately and say why.
6. **Self-review what the lint cannot check**, over every doc you touched, and
   report the result: each sentence names its actor; no noun cluster runs past
   the standard's limit; every glossary term carries its defined meaning; no
   sentence both describes and instructs; each diagram passes the standard's
   structural test and restates no adjacent list or table; the content matches
   the type marker it declares.
7. **Report and stop.** Close with the files you wrote or rewrote and their
   doc types, the lint result for each, the self-review result, and anything
   you split, moved, or propose to move.

**You edit documentation files, and nothing else ships.** Never `git commit`,
never `git push`, never open or merge a pull request — the workflow that
invoked you ships the edit in its own change. Never edit spec artifacts in the
content directory, and never edit the standard itself to pass the lint: a rule
that is wrong gets changed through the planning workflow, as a change.
