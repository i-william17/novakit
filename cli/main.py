import typer
from cli.commands.migrate import migrate_app

app = typer.Typer(help="NovaKit CLI")

app.add_typer(migrate_app, name="migrate")

def main():
    app()

if __name__ == "__main__":
    main()
