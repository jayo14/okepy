"""Structured project profile models for okepy inspection engine."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectProfile(BaseModel):
    """Machine-readable and human-displayable profile of an inspected Python backend repository."""

    project_name: str = Field(default="unknown")
    python_version: str = Field(default="Unknown")
    package_manager: str = Field(default="Unknown")
    framework: str = Field(default="None")
    project_structure: str = Field(default="Standard")
    database: str = Field(default="None")
    authentication: str = Field(default="None")
    testing_framework: str = Field(default="None")
    has_docker: bool = Field(default=False)
    has_ci: bool = Field(default=False)
    ci_provider: str = Field(default="None")
    has_redis: bool = Field(default=False)
    has_celery: bool = Field(default=False)
    env_config: str = Field(default="None")

    dependencies: list[str] = Field(default_factory=list)
    dev_dependencies: list[str] = Field(default_factory=list)
    detected_integrations: list[str] = Field(default_factory=list)
    detected_files: list[str] = Field(default_factory=list)

    maturity_score: int = Field(default=0, ge=0, le=100)
    recommendations: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, int] = Field(default_factory=dict)
