"""Maturity scoring and recommendation rules for inspected projects."""

from __future__ import annotations

from okepy.inspector.models import ProjectProfile


def calculate_maturity_score_and_recommendations(profile: ProjectProfile) -> tuple[int, list[str], dict[str, int]]:
    """Compute 0-100 maturity score and ordered recommendations based on ProjectProfile fields."""
    breakdown = {}
    recommendations = []

    if profile.framework != "None":
        breakdown["framework"] = 15
    else:
        breakdown["framework"] = 0
        recommendations.append("Adopt a modern backend framework (e.g. FastAPI, Django, Flask)")

    pkg_score = 0
    if profile.package_manager in ("uv", "poetry", "pdm"):
        pkg_score += 10
    elif profile.package_manager in ("pipenv", "pip"):
        pkg_score += 5
    if profile.python_version != "Unknown":
        pkg_score += 5
    breakdown["package_manager"] = pkg_score

    if profile.env_config in ("pydantic-settings", "python-decouple", "django-environ"):
        breakdown["env_config"] = 15
    elif profile.env_config in ("python-dotenv", ".env file"):
        breakdown["env_config"] = 10
        recommendations.append("Improve environment configuration with typed settings (e.g. pydantic-settings)")
    else:
        breakdown["env_config"] = 0
        recommendations.append("Improve environment configuration with structured .env / settings")

    if profile.testing_framework == "pytest":
        breakdown["testing"] = 15
    elif profile.testing_framework == "unittest":
        breakdown["testing"] = 10
        recommendations.append("Switch to pytest for richer testing capabilities")
    else:
        breakdown["testing"] = 0
        recommendations.append("Add test suite and testing framework (e.g. pytest)")

    if profile.has_docker:
        breakdown["docker"] = 15
    else:
        breakdown["docker"] = 0
        recommendations.append("Add Docker / Docker Compose configuration")

    if profile.has_ci:
        breakdown["ci"] = 15
    else:
        breakdown["ci"] = 0
        recommendations.append("Add CI/CD pipeline (e.g. GitHub Actions)")

    prod_score = 0
    if profile.database != "None":
        prod_score += 4
    if profile.authentication != "None":
        prod_score += 3
    if profile.has_redis or profile.has_celery:
        prod_score += 3
    breakdown["production_readiness"] = prod_score

    if profile.authentication == "None":
        recommendations.append("Add security checks and authentication layer")
    if profile.database == "None":
        recommendations.append("Configure a database or ORM integration")

    total_score = min(100, sum(breakdown.values()))
    formatted_recs = [f"[{i+1}] {rec}" for i, rec in enumerate(recommendations)]

    return total_score, formatted_recs, breakdown
