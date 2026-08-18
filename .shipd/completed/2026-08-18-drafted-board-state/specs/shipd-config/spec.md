## ADDED Requirements

### Requirement: PR mode documentation
id: pr-mode-docs

The content directory's `README.md` (the format authority) SHALL document
the `pr-mode` key: its two values `auto` and `draft`, the `auto` default
when undeclared, the layered workspace-root placement that governs every
member repo, that it governs change-shipping PRs only (metadata PRs —
epic-close derivations, initiative tagging — keep auto-merging), and the
draft-mode ship behavior (a draft PR, no auto-merge arming, merging is a
human's step). The copyable config example JSON shipped in the plugin's
build references SHALL name the optional `pr-mode` key with a pointer to
that documentation, without actively declaring a mode — copying the file
unchanged declares nothing.

#### Scenario: The format authority answers the key's usage
- **WHEN** a reader consults the content directory's `README.md` on
  `pr-mode`
- **THEN** it states both accepted values, the default, the workspace-root
  placement, the change-shipping-only scope, and the draft-mode ship
  behavior

#### Scenario: Config example points at the key
- **WHEN** a reader opens the copyable config example JSON
- **THEN** it mentions the optional `pr-mode` key and where its
  documentation lives, while copying the file unchanged declares no mode
