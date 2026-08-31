"""Top-level Typer application for okepy."""

from __future__ import annotations

import typer
from rich.table import Table

from okepy import __version__
from okepy.cli.commands.create import _create as create_app
from okepy.cli.commands.init import init_cmd
from okepy.core.registry import list_features, list_frameworks
from okepy.utils.console import console

app = typer.Typer(
    name="okepy",
    help="okepy — the production toolkit for Python backends and AI coding agents.",
    no_args_is_help=False,
    add_completion=True,
)

app.add_typer(create_app, name="create")
app.command(name="init")(init_cmd)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"okepy {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """okepy — the production toolkit for Python backends and AI coding agents."""


@app.command("list")
def list_cmd(
    what: str = typer.Argument("all", help="What to list: frameworks | features | all"),
) -> None:
    """List supported frameworks and available features."""
    if what in ("frameworks", "all"):
        table = Table(title="Frameworks", show_header=False, border_style="cyan")
        table.add_column("name", style="green")
        table.add_column("label", style="magenta")
        for fw in list_frameworks():
            table.add_row(fw.name, fw.label)
        console.print(table)
    if what in ("features", "all"):
        feats = list_features()
        table = Table(title="Features", show_header=False, border_style="cyan")
        table.add_column("name", style="green")
        table.add_column("label", style="magenta")
        if feats:
            for ft in feats:
                table.add_row(ft.name, ft.label or ft.name)
        else:
            table.add_row("—", "no built-in features registered yet (Phase 4+)")
        console.print(table)


def run() -> None:
    app()


def main_entry() -> None:  # pragma: no cover - thin wrapper
    app()


if __name__ == "__main__":  # pragma: no cover
    app()
