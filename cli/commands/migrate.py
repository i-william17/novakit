import typer
from cli.context import get_context
from cli.guards import forbid_in_production

app = typer.Typer(help="Database migrations")

@app.command("up")
def migrate_up(
    module: str = typer.Option(None, help="Module name"),
    tenant: str = typer.Option(None, help="Tenant ID"),
    force: bool = typer.Option(False, help="Force in production"),
):
    ctx = get_context()
    forbid_in_production(ctx.env, force)

    typer.echo("Running migrations")
    typer.echo(f"Module: {module or 'ALL'}")
    typer.echo(f"Tenant: {tenant or 'DEFAULT'}")

    # here we will call Alembic programmatically later


@app.command("down")
def migrate_down(
    steps: int = typer.Option(1),
    module: str = typer.Option(None),
    force: bool = typer.Option(False),
):
    ctx = get_context()
    forbid_in_production(ctx.env, force)

    typer.echo(f"Rolling back {steps} steps")
