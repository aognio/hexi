# Hexi Templates

These templates are intentionally useful, not filler.
Each template includes:
- `.hexi/config.toml`
- `.hexi/local.toml` (commented secrets)
- `Makefile` commands (`hexi-doctor`, `hexi-run`, `test`)
- starter code + starter tests

## Included templates

1. `hexi-python-lib`
2. `hexi-fastapi-service`
3. `hexi-typer-cli`
4. `hexi-data-job`
5. `hexi-agent-worker`

## Usage

Copy a template into a new directory and initialize git if needed:

```bash
cp -R templates/hexi-python-lib /tmp/my-project
cd /tmp/my-project
git init
hexi doctor
```
