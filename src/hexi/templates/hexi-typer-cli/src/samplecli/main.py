import typer

app = typer.Typer()


@app.command()
def greet(name: str = "world") -> None:
    typer.echo(f"hello {name}")


if __name__ == "__main__":
    app()
