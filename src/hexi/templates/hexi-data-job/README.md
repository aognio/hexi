# hexi-data-job

A tiny data job template with dry-run mode and Hexi integration.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make test
```

## Run job
```bash
python -m datajob.main --dry-run
```

## First Hexi task
```bash
make hexi-run TASK="Add CSV output format with tests"
```
