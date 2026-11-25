<!-- doc-type: how-to -->

# Ask shipd for help

`/s:help` answers a how-to question about shipd. It reads the installed skills
and the output of `shipd --help`, then replies with the steps and commands to
run, or an honest no. It changes no file and runs none of the commands it
suggests.

## When to use it

Use `/s:help` when you know what you want to do but not which skill or verb
does it. For example, you may want to handle a mid-spec change.

- **A fixed tour** — run [`/s:onboard`](onboard.md) instead.
- **A project decision** — run `/s:ask`. See [The oracle](oracle.md).

When you ask `/s:help` for a project decision, it names `/s:ask <decision>` and
stops.

## How to run it

Pass the question as the argument:

```sh
/s:help How do I handle a mid-spec change?
```

The skill runs these steps:

1. **Read the skill list.** It reads the frontmatter of each installed skill.
2. **Open the matches.** It opens only the skills that fit the question, and
   the references they name.
3. **Check the CLI.** It runs `shipd --help` when a verb may answer.
4. **Answer.** It opens with one verdict and backs every step with a skill or
   verb.

The skill never answers from model memory. It uses no online docs and no
repository state.

## The three verdicts

| Verdict | What follows |
|---|---|
| Supported | Numbered steps with the exact commands. |
| Partly supported | The steps, then the gap that shipd does not cover. |
| Not supported | A plain no, then the nearest option, or a note that none exists. |
