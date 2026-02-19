# hexi-typer-cli

A Typer CLI template with tests and Hexi workflow wired in.

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
make hexi-run TASK="Add greet --caps option and tests"
```
