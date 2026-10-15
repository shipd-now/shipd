## 1. The concept page

- [x] 1.1 [req: room-skill-docs] Author `docs/multi-agent-pr.md` through
      `/s:document` as a concept doc: `<!-- doc-type: concept -->` on line 1,
      title `# Multi-agent PR`, 100 lines or fewer. Open with a paragraph
      that defines a multi-agent PR as a pull request whose comment thread
      is a room where agents and people take turns on tasks, and name the
      PR room as the mechanism. Then, in this order and under their own
      headings: "Why a room" (a review finding or a question needs a reply,
      and without a protocol two agents talk over each other or a reply is
      lost); "The model" (each agent posts an Agent Card with its name and
      skills; each comment carries a Message with a task id and a state; the
      six task states `submitted`, `working`, `input-required`,
      `completed`, `failed`, `canceled`, shown in one Mermaid
      `stateDiagram-v2` with emoji-free labels and no colour; one hidden
      marker per comment with prose below; issue comments only, so review
      threads never block the merge); "Who acts when" (an agent acts only on
      an `input-required` task addressed to it, or unaddressed and matching
      a skill on its card; never on its own last message; the round cap
      `room.max_rounds`, default 6, after which the task posts `failed`);
      "Two ways a turn runs" (`/s:room` in a developer session, waiting in
      the foreground; the Actions wake installed by
      `shipd copilot add --room`, which needs no session); "The review gate
      is the first member" (the semantic review gate posts each finding as
      a task). Close with "Where next", linking `pr-room.md`,
      `room-wake-reference.md`, `customise.md` for the `room` key, and
      `semantic-review.md`. Name no verb flags.
- [x] 1.2 [req: room-skill-docs] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/multi-agent-pr.md`
      and `wc -l docs/multi-agent-pr.md`; confirm exit 0 and 100 lines or
      fewer, fixing findings until both hold.

## 2. The how-to

- [x] 2.1 [req: room-skill-docs] In `docs/pr-room.md`, change the title line
      to `# Run an agent's turn in a multi-agent PR`. Append one sentence to
      the first paragraph: `[Multi-agent PR](multi-agent-pr.md) explains the
      model this guide runs.` In "See also", add the bullet
      `- [Room wake reference](room-wake-reference.md) — the Actions wake
      that runs a turn with no session.` and the bullet
      `- [Multi-agent PR](multi-agent-pr.md) — the model.` Change nothing
      else.
- [x] 2.2 [req: room-skill-docs] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/pr-room.md`
      and `wc -l docs/pr-room.md`; confirm exit 0 and 150 lines or fewer.

## 3. The entry links

- [x] 3.1 [req: multi-agent-pr-entry-links] In `README.md`, in the "Getting
      started" section, append to the paragraph that ends "shipd offers."
      the sentence: `Running more than one agent on a pull request?
      [**docs/multi-agent-pr.md**](docs/multi-agent-pr.md) explains how they
      take turns.` Edit no other README line.
- [x] 3.2 [req: multi-agent-pr-entry-links] In `docs/what-is-shipd.md`,
      insert one paragraph between the closing Mermaid fence and the
      paragraph that opens "Today shipd builds itself": `The review gate
      also opens the pull request's room, where agents take turns on
      findings and questions. [Multi-agent PR](multi-agent-pr.md) explains
      it.` Keep it to those two sentences, wrapped at the file's width.
- [x] 3.3 [req: multi-agent-pr-entry-links] In `docs/cheatsheet.md`, in the
      `/s:room [pr]` row of the `/s: commands` table, append to the
      description cell: ` See [Multi-agent PR](multi-agent-pr.md).` Leave the
      example cell unchanged.
- [x] 3.4 [req: multi-agent-pr-entry-links] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/what-is-shipd.md docs/cheatsheet.md`
      and `wc -l docs/what-is-shipd.md`; confirm exit 0 and 100 lines or
      fewer.

## 4. Verification

- [x] 4.1 [req: *] Run
      `python3 plugins/s/skills/document/scripts/docs_lint.py docs/multi-agent-pr.md docs/pr-room.md docs/what-is-shipd.md docs/cheatsheet.md`
      and confirm exit 0; run
      `python3 -m unittest discover -s plugins/s/skills/room/tests -v` and
      confirm OK; run `git status --porcelain` and confirm no path under
      `plugins/s/` is changed, so no plugin version bump is due.
