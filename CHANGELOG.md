# CHANGELOG

## [0.4.0] - 2026-04-06

### Added
- **Infrastructure Sprint (Phase 2):**
  - Integrated `ruff` for linting and formatting and `mypy` for static type checking.
  - Created a GitHub Actions CI pipeline to automate testing and code quality checks.
  - **Finance Expansion:** Added stadium-based revenue scaling (attendance-to-revenue logic) and realistic budget caps (wage limits).
  - **Youth Expansion:** Introduced academy tiers (Elite to Minimal) and a basic scouting report generation for young prospects.
  - New test suites for Finance and Youth core expansions.

### Changed
- Unified codebase formatting using `ruff format`.
- Fixed `test_calendar.py` to account for new financial logic.
- Incremented version to `0.4.0`.

## [0.3.0] - 2026-04-06

### Added
- Egypt Cup 32-team knockout tournament (seeded draw, 5 rounds).
- Derby rivalries system with attendance and happiness multipliers.
- Ramadan calendar integration (2025-2035) with stamina and training effects.
- Full Arabic localization with RTL layout support.
- Persistent language preference in game settings.
- Initial Phase 1 stability improvements (standardized versioning, dependency cleanup).

## [0.2.0] - 2026-03-10

### Added
- Multi-season career mode with aging and youth intake.
- Asynchronous transfer negotiation system.
- Training system with 8 programs and 4 intensity levels.
- Interactive random events with financial consequences.
- Board objectives and evaluation system.

## [0.1.0] - 2026-02-27

### Added
- Initial release with MVP features.
- Core match engine simulation.
- Squad management and basic tactics.
- 18 Egyptian Premier League clubs.
