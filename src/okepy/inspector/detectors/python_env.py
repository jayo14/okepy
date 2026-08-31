"""Detector for Python version and package manager."""

from __future__ import annotations

import re
from pathlib import Path

from okepy.inspector.parsers import parse_pyproject


def detect_python_version(project_path: Path) -> str:
    """Detect python version from .python-version, pyproject.toml, runtime.txt, etc."""
    pyver_file = project_path / ".python-version"
    if pyver_file.is_file():
        try:
            ver = pyver_file.read_text(encoding="utf-8").strip()
            if ver:
                return ver
        except Exception:
            pass

    runtime_file = project_path / "runtime.txt"
    if runtime_file.is_file():
        try:
            text = runtime_file.read_text(encoding="utf-8").strip()
            match = re.search(r"python-(\d+\.\d+(?:\.\d+)?)", text, re.IGNORECASE)
            if match:
                return match.group(1)
        except Exception:
            pass

    pyproject = parse_pyproject(project_path)
    if pyproject:
        req_py = pyproject.get("project", {}).get("requires-python")
        if req_py:
            clean = re.sub(r"[^\d.]", "", str(req_py)).strip(".")
            if clean:
                return clean

        poetry_py = (
            pyproject.get("tool", {})
            .get("poetry", {})
            .get("dependencies", {})
            .get("python")
        )
        if poetry_py:
            clean = re.sub(r"[^\d.]", "", str(poetry_py)).strip(".")
            if clean:
                return clean

    return "Unknown"


def detect_package_manager(project_path: Path) -> str:
    """Detect package manager (uv, poetry, pipenv, pdm, pixi, pip) based on lockfiles/files."""
    if (project_path / "uv.lock").is_file():
        return "uv"
    if (project_path / "poetry.lock").is_file():
        return "poetry"
    if (project_path / "Pipfile.lock").is_file() or (project_path / "Pipfile").is_file():
        return "pipenv"
    if (project_path / "pdm.lock").is_file():
        return "pdm"
    if (project_path / "pixi.lock").is_file():
        return "pixi"

    pyproject = parse_pyproject(project_path)
    if pyproject:
        tool = pyproject.get("tool", {})
        if "uv" in tool:
            return "uv"
        if "poetry" in tool:
            return "poetry"
        if "pdm" in tool:
            return "pdm"
        if "flit" in tool:
            return "flit"
        if "hatch" in tool:
            return "hatch"

    if (project_path / "requirements.txt").is_file() or any(
        project_path.glob("requirements*.txt")
    ):
        return "pip"

    return "pip"
