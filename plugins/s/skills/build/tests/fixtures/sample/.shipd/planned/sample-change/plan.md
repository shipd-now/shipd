# sample-change
Status: ready

## Idea

Harden the sample auth capability by rate-limiting login, shortening the SSO
session timeout, and dropping the legacy cookie fallback.

### Motivation

Long idle sessions and an unrated login endpoint leave the sample auth
capability open to hijacking and brute-force attempts.

### Details

- Add a login rate-limit requirement.
- Shorten the SSO session timeout from 30 to 15 minutes.
- Remove the legacy cookie fallback.
- Rename `password-complexity` to `password-strength`.
- Capability: `auth`.

### Non-goals

- No change to the identity provider or the SSO handshake itself.

## Implementation

A fixture change used by the spec-engine tests to exercise all four delta
operations against a sample master library.

### Decisions

- Exercise ADDED, MODIFIED, REMOVED, and RENAMED in a single delta so merge and
  archive can be verified end-to-end.
