import typer

def forbid_in_production(env: str, force: bool = False):
    if env == "production" and not force:
        typer.echo("Command disabled in production")
        raise typer.Exit(1)
