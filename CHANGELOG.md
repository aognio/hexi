# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [0.2.0] - 2026-02-19

### Added
- New `hexi apply --plan <file>` command to execute validated ActionPlan JSON directly (debug/replay mode).
- Example ActionPlans under `examples/action_plans/`:
  - `read_only.json`
  - `write_file.json`
  - `run_tests.json`
  - `mixed_step.json`
- End-to-end tests for `hexi apply` including runlog verification and disallowed-command failure handling.

### Changed
- Version bumped from `0.1.0` to `0.2.0`.
- Template loading now supports installed-package resources (works from wheel installs, not only source checkouts).
- Project/repo URL references aligned to `https://github.com/hexi-codes/hexi`.

## [0.1.0] - 2026-02-18

### Added
- Hexi CLI commands: `init`, `onboard`, `run`, `diff`, `doctor`, `help`, `version`, `new`, `demo`, and `plan-check`.
- Rich-based colorful CLI output with panels/tables for onboarding, diagnostics, runs, and events.
- Verbose doctor diagnostics with optional live model probe (`--probe-model`).
- ActionPlan troubleshooting command (`hexi plan-check`) for inline/file JSON validation and action summaries.
- OpenRouter support via optional adapters:
  - `openrouter_http` (raw HTTP adapter)
  - `openrouter_sdk` (official SDK adapter)
- Five Hexi-native templates with built-in `.hexi` integration:
  - `hexi-python-lib`
  - `hexi-fastapi-service`
  - `hexi-typer-cli`
  - `hexi-data-job`
  - `hexi-agent-worker`
- MkDocs + Read the Docs documentation with expanded guide/reference/internal sections.
- MIT `LICENSE` file attributed to Antonio Ognio.

### Changed
- Project version bumped from `0.0.1` to `0.1.0`.
- Package metadata improved for PyPI discoverability:
  - classifiers, keywords, project URLs, license metadata, author/maintainer metadata.
- OpenRouter dependencies are optional extras:
  - `openrouter-http`
  - `openrouter-sdk`
  - `openrouter`
- `init`, `onboard`, and `doctor` now support bootstrap mode outside git repositories.
- `demo` flow improved:
  - early destination validation
  - provider connectivity preflight for ideas mode
  - stronger agentic-coder idea prompt
  - optional post-scaffold customization step
  - explicit demo disclaimer.

### Fixed
- Improved handling for non-empty destination errors by validating earlier in scaffold/demo flows.
- Reduced false failures in idea parsing with tolerant JSON extraction from model output.
- Resolved dependency compatibility issue by allowing `rich>=13.7,<15`.

[0.2.0]: https://github.com/hexi-codes/hexi/releases/tag/v0.2.0
[0.1.0]: https://github.com/hexi-codes/hexi/releases/tag/v0.1.0
