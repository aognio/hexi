# Automate Dev + Release

Hexi uses [Poe the Poet](https://poethepoet.natn.io/) for project-local automation from `pyproject.toml`.

## Why Poe

- Python-native task definitions
- zero custom shell scripts required
- team-shared commands across local/CI workflows

## Setup

```bash
pip install -e ".[dev]"
```

## Core tasks

```bash
poe test
poe docs
poe docs-build
poe check
```

## Packaging tasks

```bash
poe build
poe release
```

`poe build` performs:

- `python -m build`
- `python -m twine check dist/*`

`poe release` performs:

- `python -m build`
- `python -m twine check dist/*`
- `pytest -q`
- `mkdocs build -q`

## Publish tasks

TestPyPI:

```bash
poe publish-testpypi
```

PyPI:

```bash
poe publish-pypi
```

`publish-testpypi` uses the explicit repository URL, so it works even when `~/.pypirc` does not define a `testpypi` section.

## Recommended release flow

1. Bump version + changelog.
2. Run `poe release`.
3. Tag and push:
   - `git tag -a vX.Y.Z -m "Hexi vX.Y.Z"`
   - `git push origin main`
   - `git push origin vX.Y.Z`
4. Publish:
   - `poe publish-testpypi` (optional but recommended)
   - `poe publish-pypi`
