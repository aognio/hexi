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

## CI alignment

Hexi CI runs:

- `poe check` (tests + docs build)
- package smoke checks:
  - build wheel
  - install built wheel
  - verify packaged templates are available
  - run `hexi new` from installed wheel

This keeps local release workflow and CI validation aligned.

## Common publish issues

### Twine error: missing `testpypi` in `~/.pypirc`

Use the explicit repository URL:

```bash
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

`poe publish-testpypi` already uses this form.

### Upload rejected due to package-name similarity

PyPI can reject names considered too similar to existing projects. Rename the distribution package (`[project].name`) and re-publish with a new version.
