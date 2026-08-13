## ADDED Requirements

### Requirement: Checkpoint resume after interruption
id: checkpoint-resume

If a tour turn is interrupted or a checkpoint question comes back rejected,
then the tour SHALL resume from the last reached checkpoint on the user's
next message — re-offering that checkpoint's choices when the message does
not itself answer them — and SHALL NOT restart from the beginning or treat
the interruption as a stop. Only an explicit Stop choice SHALL end the tour.

#### Scenario: Interrupted checkpoint resumes in place
- **WHEN** a checkpoint dialog is rejected by a harness misfire and the
  user's next message asks to continue
- **THEN** the tour re-offers that same checkpoint's choices and proceeds
  from that chapter, not from chapter one

#### Scenario: Interruption is not a stop
- **WHEN** a tour turn is interrupted mid-chapter
- **THEN** the tour does not end; the next user message picks the tour up at
  the last reached checkpoint
