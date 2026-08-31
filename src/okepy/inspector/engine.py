"""Inspection engine that orchestrates project discovery and profile building."""

from __future__ import annotations

from pathlib import Path

from okepy.inspector.detectors.database_auth import detect_database_and_auth
from okepy.inspector.detectors.framework import detect_framework
from okepy.inspector.detectors.python_env import (
    detect_package_manager,
    detect_python_version,
)
from okepy.inspector.detectors.services import detect_services_and_tooling
from okepy.inspector.models import ProjectProfile
from okepy.inspector.parsers import get_all_dependencies
from okepy.inspector.scoring import calculate_maturity_score_and_recommendations


class ProjectInspector:
    """Inspection engine for analyzing an existing Python backend repository."""

    def __init__(self, project_path: Path | str | None = None) -> None:
        self.project_path = Path(project_path or Path.cwd()).resolve()

    def inspect(self) -> ProjectProfile:
        """Inspect the target repository and return a structured ProjectProfile."""
        project_name = self.project_path.name

        deps, dev_deps = get_all_dependencies(self.project_path)

        python_ver = detect_python_version(self.project_path)
        pkg_mgr = detect_package_manager(self.project_path)
        framework, structure = detect_framework(self.project_path, deps)
        database, auth = detect_database_and_auth(self.project_path, deps)
        tooling = detect_services_and_tooling(self.project_path, deps, dev_deps)

        profile = ProjectProfile(
            project_name=project_name,
            python_version=python_ver,
            package_manager=pkg_mgr,
            framework=framework,
            project_structure=structure,
            database=database,
            authentication=auth,
            testing_framework=tooling["testing_framework"],
            has_docker=tooling["has_docker"],
            has_ci=tooling["has_ci"],
            ci_provider=tooling["ci_provider"],
            has_redis=tooling["has_redis"],
            has_celery=tooling["has_celery"],
            env_config=tooling["env_config"],
            dependencies=deps,
            dev_dependencies=dev_deps,
        )

        score, recs, breakdown = calculate_maturity_score_and_recommendations(profile)
        profile.maturity_score = score
        profile.recommendations = recs
        profile.score_breakdown = breakdown

        return profile
