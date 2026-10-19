## ADDED Requirements

### Requirement: Room wake reply drops the CLI transcript
id: room-wake-reply-cleaning

Before the reply job of `plugins/s/integrations/copilot/room-wake.yml` checks for the input-required marker, it SHALL remove every tool-call transcript block from the reply. A block is a line starting with `●` and a space, plus the lines right after it whose left-trimmed text starts with `│` or `└`. The job SHALL leave every other line unchanged and SHALL add no new marker to the run prompt. A reply that is empty once its blocks are removed SHALL close the task as `failed`, the same as an empty reply.

#### Scenario: Transcript blocks are stripped from the posted reply
- **WHEN** the reply script runs on a reply holding a `● Read …` line with `│` and `└` continuation lines between two prose paragraphs
- **THEN** the stub recorded `message --state completed` with both paragraphs and none of the block lines

#### Scenario: The marker still asks back after cleaning
- **WHEN** the reply holds a transcript block and ends with `<!-- shipd-room-reply: input-required -->`
- **THEN** the stub recorded `--state input-required` with the marker and the block removed

#### Scenario: A transcript-only reply fails the task
- **WHEN** the reply holds only tool-call block lines
- **THEN** the stub recorded `close --task <id> --state failed --reason wake-runner-failed`
