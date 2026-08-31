"""The okepy init command."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from okepy.inspector.engine import ProjectInspector
from okepy.inspector.models import ProjectProfile

console = Console()


def init_cmd(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Target directory to inspect and initialize okepy in.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output project profile in machine-readable JSON format.",
    ),
) -> None:
    """Inspect an existing Python backend project and produce a structured ProjectProfile."""
    project_dir = path.resolve()
    if not project_dir.is_dir():
        if json_output:
            print(json.dumps({"error": f"Directory not found: {project_dir}"}))
        else:
            console.print(f"[bold red]Error:[/] Directory not found: {project_dir}")
        raise typer.Exit(code=1)

    if not json_output:
        console.print("[bold cyan]Scanning project...[/]")
        console.print()

    inspector = ProjectInspector(project_dir)
    profile: ProjectProfile = inspector.inspect()

    if json_output:
        print(profile.model_dump_json(indent=2))
        return

    _render_profile_terminal(profile)


def _render_profile_terminal(profile: ProjectProfile) -> None:
    """Format human-readable rich console output matching target spec."""
    labels_and_values = [
        ("Framework", profile.framework),
        ("Python", profile.python_version),
        ("Package manager", profile.package_manager),
        ("Database", profile.database),
        ("Authentication", profile.authentication),
        ("Tests", profile.testing_framework),
        ("Docker", "✓" if profile.has_docker else "✗"),
        ("CI", profile.ci_provider if profile.has_ci else "✗"),
    ]

    for label, val in labels_and_values:
        console.print(f"[bold white]{label:<16}[/] [cyan]{val}[/]")

    console.print()
    console.print(f"[bold white]Project maturity:[/] [bold green]{profile.maturity_score}/100[/]")
    console.print()

    if profile.recommendations:
        console.print("[bold white]Recommendations:[/]")
        for rec in profile.recommendations:
            console.print(f"[yellow]{rec}[/]")
