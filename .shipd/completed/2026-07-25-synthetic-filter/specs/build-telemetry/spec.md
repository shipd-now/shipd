## ADDED Requirements

### Requirement: Synthetic records are excluded from telemetry
id: synthetic-records-excluded

The telemetry tool SHALL exclude transcript records whose model is the
harness marker `<synthetic>` from the per-model usage breakdown and from
elapsed-time attribution, so no pseudo-model row appears in the table and
no wall-clock time is attributed to a non-model. Records from real models
SHALL be unaffected, including any with zero usage.

#### Scenario: Synthetic records produce no table row
- **WHEN** the build window contains records from a real model and a
  `<synthetic>` record with zero usage
- **THEN** the per-model breakdown contains only the real model and no
  `<synthetic>` row

#### Scenario: Synthetic time folds into real attribution
- **WHEN** a `<synthetic>` record sits between two records of a real model
- **THEN** the per-model times still sum to the reported total and none is
  attributed to `<synthetic>`

#### Scenario: Zero-usage real records stay visible
- **WHEN** a record from a real model reports zero tokens in the window
- **THEN** that model still appears in the breakdown
