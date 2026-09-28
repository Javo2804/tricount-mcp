# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-09-28

Documentation-only release, so the PyPI page shows the current install instructions.

### Changed

- Install instructions use `uvx tricount-mcp` from PyPI instead of installing from the GitHub
  repository (README, README.es and both quick start guides).


## [0.1.0] - 2026-09-28

First public release.

### Added

- Read tools: `connect_tricount`, `get_tricount_summary`, `list_expenses`, `get_member_detail`.
- Write tools: `create_expense` (equal split, exact amounts or ratios; standard or custom
  categories), `create_reimbursement` and `delete_entry`.
- Two-step writes: every write returns a preview first and only saves with `confirm=true`.
- Required `acting_as` on writes, validated against the tricount's members.
- Usage guide sent to any MCP client on connect (ask for the link, ask who the user is, confirm
  before saving).
- Splits in whole currency units, so shares always add up to the total.
- Local (stdio) and HTTP (streamable HTTP, stateless) modes, plus a `Dockerfile`.
- Audit log of confirmed writes as JSON on stderr (Cloud Logging on Cloud Run).
- Install with `uvx`, quick start guides in English and Spanish.

[0.1.1]: https://github.com/Javo2804/tricount-mcp/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Javo2804/tricount-mcp/releases/tag/v0.1.0