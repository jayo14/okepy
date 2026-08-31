"""Detector for databases, ORMs, and authentication mechanisms."""

from __future__ import annotations

from pathlib import Path

DB_MAP = {
    "psycopg2": "PostgreSQL",
    "psycopg2-binary": "PostgreSQL",
    "psycopg": "PostgreSQL",
    "asyncpg": "PostgreSQL",
    "mysqlclient": "MySQL",
    "pymysql": "MySQL",
    "aiomysql": "MySQL",
    "pymongo": "MongoDB",
    "motor": "MongoDB",
    "redis": "Redis",
}

AUTH_MAP = {
    "pyjwt": "JWT",
    "python-jose": "JWT",
    "auth0-python": "Auth0",
    "django-allauth": "OAuth2 / Allauth",
    "python-social-auth": "Social OAuth",
    "fastapi-users": "JWT / Session",
    "flask-jwt-extended": "JWT",
    "flask-login": "Session",
}


def detect_database_and_auth(
    project_path: Path, dependencies: list[str]
) -> tuple[str, str]:
    """Detect primary database and authentication method."""
    deps_set = {d.lower() for d in dependencies}

    detected_db = "None"
    for dep, db_name in DB_MAP.items():
        if dep in deps_set and db_name != "Redis":
            detected_db = db_name
            break

    if detected_db == "None":
        if "sqlite3" in deps_set or _has_file_content(project_path, "sqlite3"):
            detected_db = "SQLite"
        elif "tortoise-orm" in deps_set or "ormar" in deps_set:
            detected_db = "SQLite / Relational"

    detected_auth = "None"
    found_auths = []
    for dep, auth_name in AUTH_MAP.items():
        if dep in deps_set:
            found_auths.append(auth_name)

    if found_auths:
        detected_auth = " / ".join(dict.fromkeys(found_auths))
    elif "django" in deps_set or (project_path / "manage.py").is_file():
        if _has_file_content(project_path, "rest_framework_simplejwt") or "djangorestframework-simplejwt" in deps_set:
            detected_auth = "JWT"
        else:
            detected_auth = "Session (Django)"

    return detected_db, detected_auth


def _has_file_content(project_path: Path, keyword: str) -> bool:
    search_dirs = [project_path, project_path / "src"]
    for sdir in search_dirs:
        if not sdir.is_dir():
            continue
        for py_file in sdir.glob("**/*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if keyword in content:
                    return True
            except Exception:
                pass
    return False
