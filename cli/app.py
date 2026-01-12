import typer
from cli.commands import migrate

def create_cli() -> typer.Typer:
    app = typer.Typer(
        name="nova",
        help="NovaKit Framework CLI",
        add_completion=False,
    )

    app.add_typer(migrate.app, name="migrate")

    return app
