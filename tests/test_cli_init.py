"""CLI integration tests for okepy init command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from okepy.cli.app import app

runner = CliRunner()


def test_cli_init_plain_output(tmp_path: Path):
    project_dir = tmp_path / "my-api"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text('[project]\nname = "my-api"\ndependencies = ["fastapi"]\n', encoding="utf-8")

    result = runner.invoke(app, ["init", "--path", str(project_dir)])
    assert result.exit_code == 0
    assert "Scanning project..." in result.stdout
    assert "Framework" in result.stdout


def test_cli_init_json_output(tmp_path: Path):
    project_dir = tmp_path / "my-flask-app"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("flask>=3.0\npytest\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "-p", str(project_dir), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["project_name"] == "my-flask-app"
    assert data["framework"] == "Flask"


def test_cli_init_non_existent_path():
    result = runner.invoke(app, ["init", "-p", "/non/existent/path/okepy"])
    assert result.exit_code == 1
    assert "Directory not found" in result.stdout
