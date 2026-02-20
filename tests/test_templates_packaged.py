from __future__ import annotations

from importlib.resources import files


def test_packaged_templates_present() -> None:
    templates_root = files("hexi").joinpath("templates")
    assert templates_root.is_dir()

    required = [
        "hexi-python-lib",
        "hexi-fastapi-service",
        "hexi-typer-cli",
        "hexi-data-job",
        "hexi-agent-worker",
    ]
    for name in required:
        template_dir = templates_root.joinpath(name)
        assert template_dir.is_dir(), f"missing template: {name}"
        assert template_dir.joinpath("pyproject.toml").is_file(), f"missing pyproject.toml in {name}"
