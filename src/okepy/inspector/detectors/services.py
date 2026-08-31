"""Detector for background services, docker, CI/CD, testing, and environment config."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def detect_services_and_tooling(
    project_path: Path, dependencies: list[str], dev_dependencies: list[str]
) -> dict[str, Any]:
    """Detect Redis, Celery, Docker, CI/CD, testing framework, and env config."""
    all_deps = {d.lower() for d in dependencies + dev_dependencies}

    testing_fw = "None"
    if "pytest" in all_deps or (project_path / "pytest.ini").is_file():
        testing_fw = "pytest"
    elif "unittest" in all_deps or (project_path / "tests").is_dir():
        testing_fw = "unittest"

    has_redis = "redis" in all_deps or "aioredis" in all_deps
    has_celery = "celery" in all_deps

    has_docker = (
        (project_path / "Dockerfile").is_file()
        or (project_path / "docker-compose.yml").is_file()
        or (project_path / "docker-compose.yaml").is_file()
        or (project_path / "compose.yaml").is_file()
        or (project_path / "compose.yml").is_file()
    )

    has_ci = False
    ci_provider = "None"
    if (project_path / ".github" / "workflows").is_dir():
        has_ci = True
        ci_provider = "GitHub Actions"
    elif (project_path / ".gitlab-ci.yml").is_file():
        has_ci = True
        ci_provider = "GitLab CI"
    elif (project_path / "bitbucket-pipelines.yml").is_file():
        has_ci = True
        ci_provider = "Bitbucket Pipelines"
    elif (project_path / ".circleci").is_dir():
        has_ci = True
        ci_provider = "CircleCI"

    env_config = "None"
    if "pydantic-settings" in all_deps:
        env_config = "pydantic-settings"
    elif "python-decouple" in all_deps:
        env_config = "python-decouple"
    elif "django-environ" in all_deps:
        env_config = "django-environ"
    elif "python-dotenv" in all_deps:
        env_config = "python-dotenv"
    elif (project_path / ".env.example").is_file() or (project_path / ".env").is_file():
        env_config = ".env file"

    return {
        "testing_framework": testing_fw,
        "has_redis": has_redis,
        "has_celery": has_celery,
        "has_docker": has_docker,
        "has_ci": has_ci,
        "ci_provider": ci_provider,
        "env_config": env_config,
    }
