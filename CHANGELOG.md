# Changelog

This project uses Semantic Versioning (MAJOR.MINOR.PATCH). Versions below describe selected development milestones, not previously published releases.

## [Unreleased]

## [0.3.0] - 2026-11-18 (release candidate milestone)

- Added TiDB Cloud SSL support, Gunicorn and Render deployment instructions (PR #29).
- Added availability report, system test and test-report documentation (PR #30).
- Split CI into lint/syntax, unit tests, smoke tests, statement coverage and branch coverage jobs; enabled manual runs (PR #31).
- Added version metadata and release instructions.

Release publication requires passing CI and verification of the deployed application.

## [0.2.0] - 2026-11-17

- Added product deletion, mandatory/numeric validation and case-insensitive duplicate prevention (PR #26).
- Added availability reporting and filtering (PR #27).
- Added automated coverage reporting (PR #28).

Historical snapshot: `9581c436a7d305e350f6799792805a2819728eea`.

## [0.1.0] - 2026-10-28

- Added authentication, role-based access, inventory view/search and product creation/update.
- Added dashboard UI and stock availability classification.
- Integrated inventory branch (PR #24) and Sprint 1 automated tests.

Historical snapshot: `0b6a41f2914c48cc2601cddddb997c37aacffab0`.

[Unreleased]: https://github.com/Inventory-Management-System-G16/Electronics_Store_Inventory_Management_System/commits/main/
