## ADDED Requirements

### Requirement: Pointer crops ground an intent's target
id: video-skill-cursor-crop

Where a cited frame's `frames.json` entry carries a `cursor` object, the
`/s:video-ingest` skill SHALL read that entry's crop image in addition to the
full frame, and SHALL treat the element under the pointer as the strongest
available evidence of the intent's target. Where a cited frame carries no
`cursor` object, the skill SHALL ground the intent on the full frame alone and
SHALL NOT assert where the speaker was pointing. Where a `cursor` object's
`origin` is `carried`, the skill SHALL treat the position as the pointer's last
known resting place rather than as a gesture made at that moment.

#### Scenario: The crop identifies the intent's target
- **WHEN** an intent's nearest frame carries a `cursor` object
- **THEN** the skill reads the crop as well as the full frame and names the
  element under the pointer as the intent's target

#### Scenario: A frame with no pointer is not embellished
- **WHEN** an intent's nearest frame carries no `cursor` object
- **THEN** the brief grounds the intent on the full frame and makes no claim
  about where the speaker was pointing

#### Scenario: A carried position is not overstated
- **WHEN** a cited frame's `cursor` object records an `origin` of `carried`
- **THEN** the brief treats it as the pointer's resting position rather than as
  a gesture made when the words were spoken
