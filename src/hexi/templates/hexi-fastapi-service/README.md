# hexi-fastapi-service

A production-lite FastAPI service template with Hexi integration.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make test
make hexi-doctor
```

## First Hexi task
```bash
make hexi-run TASK="Add /version endpoint and tests"
```
