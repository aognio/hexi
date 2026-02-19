from typer.testing import CliRunner

from datajob.main import app


def test_dry_run() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.stdout
