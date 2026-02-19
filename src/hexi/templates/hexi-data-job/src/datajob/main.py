from pathlib import Path

import typer

app = typer.Typer()


@app.command()
def run(dry_run: bool = True) -> None:
    output = Path("data/output/report.txt")
    output.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        typer.echo("dry-run: no output written")
        return
    output.write_text("report generated\n", encoding="utf-8")
    typer.echo(f"wrote {output}")


if __name__ == "__main__":
    app()
