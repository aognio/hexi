from typer.testing import CliRunner

from samplecli.main import app


def test_greet() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["greet", "Hexi"])
    assert result.exit_code == 0
    assert "hello Hexi" in result.stdout
