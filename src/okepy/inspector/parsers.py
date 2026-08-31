"""Parsers for project config, dependency, and manifest files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import tomlkit


def parse_pyproject(project_path: Path) -> dict[str, Any]:
    """Parse pyproject.toml if present, returning raw data or empty dict."""
    pyproject_file = project_path / "pyproject.toml"
    if not pyproject_file.is_file():
        return {}
    try:
        content = pyproject_file.read_text(encoding="utf-8")
        return dict(tomlkit.parse(content))
    except Exception:
        return {}


def parse_requirements_txt(file_path: Path) -> list[str]:
    """Extract package names from a requirements.txt style file."""
    if not file_path.is_file():
        return []
    packages = []
    try:
        content = file_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            pkg = re.split(r"[;<=>!~]", line)[0].strip()
            if pkg:
                packages.append(pkg.lower())
    except Exception:
        pass
    return packages


def get_all_dependencies(project_path: Path) -> tuple[list[str], list[str]]:
    """Gather main and dev dependency package names from pyproject.toml, requirements, etc."""
    deps: set[str] = set()
    dev_deps: set[str] = set()

    pyproject = parse_pyproject(project_path)
    if pyproject:
        project = pyproject.get("project", {})
        if isinstance(project, dict):
            for d in project.get("dependencies", []):
                pkg = re.split(r"[;<=>!~]", str(d))[0].strip()
                if pkg:
                    deps.add(pkg.lower())
            opt_deps = project.get("optional-dependencies", {})
            if isinstance(opt_deps, dict):
                for _group, group_deps in opt_deps.items():
                    for d in group_deps:
                        pkg = re.split(r"[;<=>!~]", str(d))[0].strip()
                        if pkg:
                            dev_deps.add(pkg.lower())

        poetry = pyproject.get("tool", {}).get("poetry", {})
        if isinstance(poetry, dict):
            p_deps = poetry.get("dependencies", {})
            if isinstance(p_deps, dict):
                for k in p_deps:
                    if k.lower() != "python":
                        deps.add(k.lower())
            p_dev = poetry.get("group", {}).get("dev", {}).get("dependencies", {})
            if isinstance(p_dev, dict):
                for k in p_dev:
                    dev_deps.add(k.lower())

        uv_tool = pyproject.get("tool", {}).get("uv", {})
        if isinstance(uv_tool, dict):
            dev_group = uv_tool.get("dev-dependencies", [])
            for d in dev_group:
                pkg = re.split(r"[;<=>!~]", str(d))[0].strip()
                if pkg:
                    dev_deps.add(pkg.lower())

    for req_file in project_path.glob("requirements*.txt"):
        parsed = parse_requirements_txt(req_file)
        if "dev" in req_file.name.lower() or "test" in req_file.name.lower():
            dev_deps.update(parsed)
        else:
            deps.update(parsed)

    req_dir = project_path / "requirements"
    if req_dir.is_dir():
        for req_file in req_dir.glob("*.txt"):
            parsed = parse_requirements_txt(req_file)
            if "dev" in req_file.name.lower() or "test" in req_file.name.lower():
                dev_deps.update(parsed)
            else:
                deps.update(parsed)

    return sorted(deps), sorted(dev_deps)
