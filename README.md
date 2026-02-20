# Hexi v0.3.0

![Hexi Saturn Hexagon](https://raw.githubusercontent.com/aognio/hexi/main/assets/images/hexi-saturn-hexagon-1024x1024.png)

Hexi is a minimal, contract-driven (hexagonal) coding-agent runtime and CLI.
It runs exactly one agent step per invocation against a local git repository.

## Test Drive (5 Minutes)
Run this in any local git repo you can safely modify.

1. Install Hexi:
```bash
pip install -e .
```
Optional OpenRouter support:
```bash
pip install -e ".[openrouter]"
```

2. Initialize Hexi files:
```bash
hexi init
```

3. Onboard provider/model and key:
```bash
hexi onboard
```
When prompted, pick any provider. For OpenRouter providers, install the optional extra and provide `OPENROUTER_API_KEY`.

4. Verify setup:
```bash
hexi doctor
```
Expected: provider/model printed and `Doctor check passed`.

5. Run one agent step:
```bash
hexi run "Add one tiny test for an existing function and run pytest"
```

6. Inspect what changed:
```bash
hexi diff
tail -n 20 .hexi/runlog.jsonl
```

7. If you want to switch providers later:
```bash
hexi onboard
```
Re-run onboarding to update `.hexi/local.toml`.

## What it is
- Python package (PyPI distribution): `hexicodes`
- Core contracts in `hexi.core`
- Side-effect adapters in `hexi.adapters`
- One-step execution with structured event logging to `.hexi/runlog.jsonl`

## What it is not
- No daemon, no background workers, no web UI
- No MCP server and no SQLite in v0.3.0
- No multi-agent orchestration


## Install
```bash
pip install -e .
```

### OpenRouter support (optional)
- HTTP adapter only (`openrouter_http` provider):
```bash
pip install -e ".[openrouter-http]"
```
- SDK adapter only (`openrouter_sdk` provider):
```bash
pip install -e ".[openrouter-sdk]"
```
- Both OpenRouter adapters:
```bash
pip install -e ".[openrouter]"
```

Dev/test dependencies:
```bash
pip install -e ".[dev]"
```

## Pythonic Task Automation (`poe`)
Hexi includes a project-local task runner using [Poe the Poet](https://poethepoet.natn.io/), so you do not need to memorize long command chains.

Install dev tooling:
```bash
pip install -e ".[dev]"
```

Common tasks:
```bash
poe test            # run pytest
poe docs            # mkdocs serve (local docs server)
poe docs-build      # mkdocs static build
poe check           # tests + docs build
poe build           # package build + twine check
poe release         # build + twine check + tests + docs build
poe publish-testpypi  # upload dist/* to TestPyPI via repository URL
poe publish-pypi      # upload dist/* to PyPI
```

## CLI
- `hexi --help` or `hexi help` : show command help
- `hexi -v ...` / `hexi -vv ...` : increase runtime verbosity (trace lines + richer event payloads)
- `hexi --version` or `hexi version` : print installed version
- `hexi init` : create `.hexi/config.toml`, `.hexi/local.toml`, `.hexi/runlog.jsonl`
- `hexi onboard` : interactive setup for provider/model and optional local key paste
- `hexi new` : scaffold a project from built-in Hexi templates (non-interactive by default)
- `hexi demo` : fancy interactive flow with random/model-generated ideas and template scaffolding
- `hexi run "<task>"` : execute one agent step and emit structured events
- `hexi apply --plan plan.json` : execute a validated ActionPlan file directly (debug/replay mode)
- `hexi diff` : show current git diff
- `hexi doctor` : verbose diagnostics; use `--probe-model` for live “What model are you?” check
- `hexi plan-check --file plan.json` : validate/troubleshoot ActionPlan JSON directly

## Documentation (MkDocs + Read the Docs)
Build docs locally:
```bash
pip install -e ".[docs]"
mkdocs serve
```

Read the Docs config is in `.readthedocs.yml`.

CI runs on GitHub Actions and validates:
- `poe check` (tests + docs build)
- package smoke flow (build wheel, install wheel, verify templates, run `hexi new`)

## Configuration design choices
Hexi uses layered TOML configuration:
1. `.hexi/config.toml` (repo defaults)
2. `.hexi/local.toml` (local machine overrides)
3. Environment variables (recommended for secrets)

For secrets, env vars are preferred. `hexi onboard` can write keys to `.hexi/local.toml` for local/testing convenience.

## Config shape (`.hexi/config.toml`)
```toml
[model]
provider = "openai_compat" # openrouter_http | openrouter_sdk | openai_compat | anthropic_compat
model = "gpt-4o-mini"

[providers.openrouter_http]
base_url = "https://openrouter.ai/api/v1"
api_style = "openai" # openai | anthropic

[providers.openrouter_sdk]
base_url = "https://openrouter.ai/api/v1"

[providers.openai_compat]
base_url = "https://api.openai.com/v1"

[providers.anthropic_compat]
base_url = "https://api.anthropic.com"

[policy]
allow_commands = ["git status", "git diff", "pytest", "python -m pytest"]
max_diff_chars = 4000
max_file_read_chars = 4000
```

## Local override example (`.hexi/local.toml`)
```toml
[model]
provider = "openrouter_http"
model = "anthropic/claude-sonnet-4-6"

[providers.openrouter_http]
api_style = "anthropic"

[secrets]
openrouter_api_key = "..."
```

## Env vars
- `OPENROUTER_API_KEY` for `openrouter_http` and `openrouter_sdk`
- `OPENAI_API_KEY` for `openai_compat`
- `ANTHROPIC_API_KEY` for `anthropic_compat`

## Packaging
- Distribution name: `hexicodes`
- Console script: `hexi`
- Optional extras:
  - `openrouter-http`
  - `openrouter-sdk`
  - `openrouter`
  - `docs`
  - `dev`

## Included example projects
- `examples/todo_refiner` : minimal CLI-wrapper agent integration
- `examples/embedded_step` : direct embedded `RunStepService` usage
- `examples/policy_loop` : multi-step user-gated loop using repeated `hexi run`

## Example ActionPlans (`hexi apply`)
- `examples/action_plans/read_only.json` : inspect file + emit progress
- `examples/action_plans/write_file.json` : create a file in-repo
- `examples/action_plans/run_tests.json` : run `pytest -q`
- `examples/action_plans/mixed_step.json` : read + write + run + emit
- `examples/action_plans/list_files.json` : list files by path/glob
- `examples/action_plans/search_text.json` : search text matches by path/glob

Try one now:
```bash
hexi plan-check --file examples/action_plans/mixed_step.json
hexi apply --plan examples/action_plans/mixed_step.json --task "ActionPlan debug run"
```

## Included Hexi-native templates
- `templates/hexi-python-lib` : tested library starter with Hexi wiring
- `templates/hexi-fastapi-service` : FastAPI service starter with Hexi wiring
- `templates/hexi-typer-cli` : Typer CLI starter with Hexi wiring
- `templates/hexi-data-job` : data job starter with dry-run and Hexi wiring
- `templates/hexi-agent-worker` : embedded Hexi runtime starter

## Provenance

Made with ❤️ from 🇵🇪. El Perú es clave 🔑.
