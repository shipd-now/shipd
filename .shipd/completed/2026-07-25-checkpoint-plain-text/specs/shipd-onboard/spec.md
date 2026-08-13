## ADDED Requirements

### Requirement: Plain-text tour prompts
id: plain-text-tour-prompts

Because the harness can drop lesson text sharing a turn with a dialog, the
tour SHALL offer its chapter menu, every chapter checkpoint, and the
sandbox offer as plain-text numbered prompts in the same message as the
greeting or lesson they follow, answered by the user's typed reply, with
the recommended default named first. The tour SHALL NOT issue an
AskUserQuestion in any turn that carries lesson or chapter content;
dialogs MAY remain only for prose-free prompts such as the sandbox
cleanup offer.

#### Scenario: Checkpoint is typed, lesson stays visible
- **WHEN** a chapter has been taught and the tour reaches its checkpoint
- **THEN** the lesson and a numbered continue/re-explain/jump/stop prompt
  form one plain-text message and the choice is read from the user's typed
  reply, with no AskUserQuestion issued

#### Scenario: Prose-free prompts may stay dialogs
- **WHEN** the sandbox session ends and the tour offers delete-or-keep
- **THEN** that prompt may be an AskUserQuestion, since its turn carries no
  lesson content
