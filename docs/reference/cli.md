# CLI Reference

## `hexi --help` / `hexi help`

Shows command help. Hexi also displays help when run without arguments.

Use global verbosity flags on any command:

- `-v`: include trace lines and richer payload output
- `-vv`: include maximal payload output

## `hexi --version` / `hexi version`

Prints the installed Hexi version.

## `hexi init`

Creates repository-scoped state files:

- `.hexi/config.toml`
- `.hexi/local.toml`
- `.hexi/runlog.jsonl`

Works in bootstrap mode outside git repos.

## `hexi onboard`

Interactive setup for provider/model and optional local key storage.
Works in bootstrap mode outside git repos.

## `hexi new`

Scaffolds a project from a built-in template.

Key options:

- `--template`
- `--name`
- `--path`
- `--git-init`
- `--interactive`
- `--force`

## `hexi demo`

Runs a fancy interactive flow:

- random idea mode,
- model-generated 3-idea mode,
- custom prompt mode,

then scaffolds a selected template.

## `hexi run "<task>"`

Runs one agent step.

Exit codes:

- `0`: successful run
- `1`: run completed with failure state
- `2`: environment/setup error

## `hexi apply --plan plan.json`

Executes one validated ActionPlan JSON file directly.

Use this for:

- debugging parser/executor behavior
- replaying a saved plan without model calls
- deterministic policy and workspace troubleshooting

## `hexi diff`

Prints bounded git diff.

## `hexi doctor`

Checks:

- repo context
- active provider/model
- config + local config paths
- API key source (`env`, `local`, `none`)

Optional live probe:

- `hexi doctor --probe-model`
