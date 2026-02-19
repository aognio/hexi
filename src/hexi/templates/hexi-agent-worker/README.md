# hexi-agent-worker

A minimal embedded Hexi worker template.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
make hexi-doctor
```

## Run embedded worker
```bash
python worker/main.py "Add one parser edge test"
```

## First Hexi task (CLI)
```bash
make hexi-run TASK="Improve worker logging"
```
