"""Detector for framework and project layout conventions."""

from __future__ import annotations

from pathlib import Path

FRAMEWORK_MAP = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "litestar": "Litestar",
    "sanic": "Sanic",
    "tornado": "Tornado",
    "starlette": "Starlette",
    "bottle": "Bottle",
    "pyramid": "Pyramid",
    "aiohttp": "Aiohttp",
    "masonite": "Masonite",
}


def detect_framework(project_path: Path, dependencies: list[str]) -> tuple[str, str]:
    """Detect main web framework and project structure layout."""
    deps_set = {d.lower() for d in dependencies}

    detected_fw = "None"
    for dep, name in FRAMEWORK_MAP.items():
        if dep in deps_set:
            detected_fw = name
            break

    if detected_fw == "None":
        if (project_path / "manage.py").is_file():
            detected_fw = "Django"
        elif _has_file_content(project_path, "FastAPI"):
            detected_fw = "FastAPI"
        elif _has_file_content(project_path, "Flask"):
            detected_fw = "Flask"

    structure = "Standard"
    if (project_path / "src").is_dir():
        structure = "src-layout"
    elif (project_path / "apps").is_dir():
        structure = "multi-app"
    elif (project_path / "config" / "settings").is_dir():
        structure = "split-settings"

    return detected_fw, structure


def _has_file_content(project_path: Path, keyword: str) -> bool:
    """Check python files for keyword imports in root or src."""
    search_dirs = [project_path, project_path / "src"]
    for sdir in search_dirs:
        if not sdir.is_dir():
            continue
        for py_file in sdir.glob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if keyword in content:
                    return True
            except Exception:
                pass
    return False
