"""Unit tests for the okepy inspector engine and detectors."""

from __future__ import annotations

from pathlib import Path

from okepy.inspector.engine import ProjectInspector
from okepy.inspector.models import ProjectProfile


def test_fastapi_fixture_inspection(tmp_path: Path):
    """Test inspection of a mock FastAPI project."""
    project_dir = tmp_path / "my-fastapi-app"
    project_dir.mkdir()

    pyproject_content = (
        "[project]\n"
        'name = "my-fastapi-app"\n'
        'requires-python = ">=3.13"\n'
        'dependencies = ["fastapi>=0.110.0", "uvicorn>=0.28.0", "asyncpg>=0.29.0", "pyjwt>=2.8.0", "pydantic-settings>=2.2.0", "redis>=5.0.0"]\n\n'
        "[tool.uv]\n"
        'dev-dependencies = ["pytest>=8.0.0"]\n'
    )
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
    (project_dir / "uv.lock").touch()
    (project_dir / "Dockerfile").touch()

    workflows = project_dir / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").touch()

    inspector = ProjectInspector(project_dir)
    profile: ProjectProfile = inspector.inspect()

    assert profile.project_name == "my-fastapi-app"
    assert profile.framework == "FastAPI"
    assert profile.python_version == "3.13"
    assert profile.package_manager == "uv"
    assert profile.database == "PostgreSQL"
    assert profile.authentication == "JWT"
    assert profile.testing_framework == "pytest"
    assert profile.has_docker is True
    assert profile.has_ci is True
    assert profile.ci_provider == "GitHub Actions"
    assert profile.has_redis is True
    assert profile.env_config == "pydantic-settings"
    assert profile.maturity_score >= 80


def test_django_fixture_inspection(tmp_path: Path):
    """Test inspection of a mock Django project."""
    project_dir = tmp_path / "my-django-app"
    project_dir.mkdir()

    reqs = "django>=5.0\npsycopg2-binary>=2.9\ndjangorestframework-simplejwt>=5.3\ncelery>=5.3\npython-decouple>=3.8\n"
    (project_dir / "requirements.txt").write_text(reqs, encoding="utf-8")
    (project_dir / "manage.py").touch()
    (project_dir / ".python-version").write_text("3.12.0\n", encoding="utf-8")

    inspector = ProjectInspector(project_dir)
    profile: ProjectProfile = inspector.inspect()

    assert profile.framework == "Django"
    assert profile.python_version == "3.12.0"
    assert profile.package_manager == "pip"
    assert profile.database == "PostgreSQL"
    assert profile.authentication == "JWT"
    assert profile.has_celery is True
    assert profile.env_config == "python-decouple"


def test_empty_project_inspection(tmp_path: Path):
    """Test inspection of an empty project directory."""
    project_dir = tmp_path / "empty-proj"
    project_dir.mkdir()

    inspector = ProjectInspector(project_dir)
    profile: ProjectProfile = inspector.inspect()

    assert profile.project_name == "empty-proj"
    assert profile.framework == "None"
    assert profile.database == "None"
    assert profile.authentication == "None"
    assert profile.maturity_score < 50
    assert len(profile.recommendations) > 0
