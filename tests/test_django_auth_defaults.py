"""Integration tests for Django REST_FRAMEWORK auth defaults.

Verifies the template generates the correct permission/authentication classes
depending on whether the ``auth`` feature is selected.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from okepy.core.config import (
    AuthProvider,
    Database,
    Deployment,
    FeatureName,
    Framework,
    ProjectConfig,
    ProjectType,
    default_config,
)
from okepy.core.context import build_context
from okepy.features import AuthFeature, JWTFeature, RedisFeature, RefreshTokenFeature  # noqa: F401
from okepy.frameworks.django import DjangoFramework


@pytest.fixture
def django_framework():
    return DjangoFramework()


def _project_dir(name: str) -> Path:
    return Path(f"/tmp/okepy-test-auth-{name}")


def _cleanup(path: Path) -> None:
    if path.exists():
        import shutil

        shutil.rmtree(path)


def test_default_scaffold_includes_auth_rest_framework(django_framework):
    """--defaults (which includes auth) should generate IsAuthenticated + JWT."""
    target = _project_dir("with-auth")
    _cleanup(target)
    cfg = default_config("with-auth-test")
    cfg.framework = Framework.DJANGO
    ctx = build_context(cfg, base_dir=target.parent)
    django_framework.scaffold(ctx)
    settings = ctx.project_dir / "config" / "settings" / "base.py"
    assert settings.exists()
    content = settings.read_text()
    assert "IsAuthenticated" in content
    assert "JWTAuthentication" in content
    assert "AllowAny" not in content
    _cleanup(target)


def test_no_auth_scaffold_uses_allowany(django_framework):
    """Scaffold without auth should generate AllowAny and empty auth classes."""
    target = _project_dir("no-auth")
    _cleanup(target)
    cfg = ProjectConfig(
        name="no-auth-test",
        project_type=ProjectType.API,
        framework=Framework.DJANGO,
        database=Database.SQLITE,
        auth_providers=[],
        api_auth=[],
        background_jobs=[],
        storage=[],
        api_docs=[],
        docker=[],
        testing=[],
        deployment=Deployment.NONE,
    )
    ctx = build_context(cfg, base_dir=target.parent)
    django_framework.scaffold(ctx)
    settings = ctx.project_dir / "config" / "settings" / "base.py"
    assert settings.exists()
    content = settings.read_text()
    assert "AllowAny" in content
    assert "IsAuthenticated" not in content
    assert (
        '"DEFAULT_AUTHENTICATION_CLASSES": ()' in content
        or '"DEFAULT_AUTHENTICATION_CLASSES": ()' in content
    )
    _cleanup(target)


@pytest.mark.slow
def test_no_auth_health_check_accessible(tmp_path):
    """Generate a Django project without auth, run manage.py check -> exit 0."""
    cfg = ProjectConfig(
        name="no-auth-health",
        project_type=ProjectType.API,
        framework=Framework.DJANGO,
        database=Database.SQLITE,
        auth_providers=[],
        api_auth=[],
        background_jobs=[],
        storage=[],
        api_docs=[],
        docker=[],
        testing=[],
        deployment=Deployment.NONE,
    )
    ctx = build_context(cfg, base_dir=tmp_path)
    DjangoFramework().scaffold(ctx)
    # Create a minimal .env so decouple doesn't complain
    (ctx.project_dir / ".env").write_text("SECRET_KEY=test\nDEBUG=True\n")
    # Run manage.py check
    result = subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=ctx.project_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"manage.py check failed:\n{result.stdout}\n{result.stderr}"


@pytest.fixture
def ctx_with_auth():
    cfg = default_config("testproj")
    cfg.framework = Framework.DJANGO
    return build_context(cfg)


@pytest.fixture
def ctx_no_auth():
    cfg = ProjectConfig(name="testproj", framework=Framework.DJANGO, database=Database.SQLITE)
    return build_context(cfg)


def test_default_env_includes_email_vars_when_auth_enabled(ctx_with_auth):
    from okepy.core.generator import _default_env

    env = _default_env(ctx_with_auth)
    assert "EMAIL_HOST=localhost" in env
    assert "EMAIL_PORT=1025" in env
    assert "FRONTEND_URL=http://localhost:3000" in env
    assert "SITE_NAME=testproj" in env
    assert "EMAIL_HOST_USER=" in env


def test_default_env_redir_url_appears_once(ctx_with_auth):
    """REDIS_URL should appear exactly once even with redis+celery selected."""
    from okepy.core.generator import _default_env

    env = _default_env(ctx_with_auth)
    # Default config includes both redis and celery
    count = env.count("REDIS_URL")
    assert count == 1, f"REDIS_URL appears {count} times, expected 1"


def test_default_env_no_auth_omits_jwt_vars(ctx_no_auth):
    from okepy.core.generator import _default_env

    env = _default_env(ctx_no_auth)
    assert "JWT_SECRET_KEY" not in env
    assert "EMAIL_HOST" not in env


# --- dependency resolution integration tests -------------------------------


def test_celery_only_auto_includes_redis_files(tmp_path):
    """Scaffolding with only 'celery' selected should generate contrib/redis.py."""
    from okepy.core.registry import order_features

    cfg = ProjectConfig(
        name="celery-only",
        project_type=ProjectType.API,
        framework=Framework.DJANGO,
        database=Database.SQLITE,
        background_jobs=[FeatureName.CELERY],  # celery only, no explicit redis
    )
    ctx = build_context(cfg, base_dir=tmp_path)
    DjangoFramework().scaffold(ctx)

    # order_features should auto-include redis
    resolved = order_features(ctx.features)
    assert "redis" in resolved
    assert resolved.index("redis") < resolved.index("celery")

    # RedisFeature.install should generate contrib/redis.py
    RedisFeature().install(ctx)
    redis_py = ctx.project_dir / "contrib" / "redis.py"
    assert redis_py.exists()


def test_auth_only_auto_includes_jwt(tmp_path):
    """Selecting only auth should auto-include jwt and generate tokens.py."""
    from okepy.core.registry import order_features

    cfg = ProjectConfig(
        name="auth-only",
        project_type=ProjectType.API,
        framework=Framework.DJANGO,
        database=Database.SQLITE,
        auth_providers=[AuthProvider.EMAIL_PASSWORD],  # implies auth feature
    )
    ctx = build_context(cfg, base_dir=tmp_path)
    DjangoFramework().scaffold(ctx)

    resolved = order_features(ctx.features)
    assert "jwt" in resolved
    assert resolved.index("jwt") < resolved.index("auth")

    JWTFeature().install(ctx)
    tokens_py = ctx.project_dir / "tokens.py"
    assert tokens_py.exists()


def test_social_auto_includes_auth_and_jwt_transitive(tmp_path):
    """Social should auto-include auth and jwt (transitive via auth)."""
    from okepy.core.registry import order_features

    cfg = ProjectConfig(
        name="social-only",
        project_type=ProjectType.API,
        framework=Framework.DJANGO,
        database=Database.SQLITE,
        auth_providers=[AuthProvider.GOOGLE],  # social implied, auth not explicit
    )
    ctx = build_context(cfg, base_dir=tmp_path)
    DjangoFramework().scaffold(ctx)
    # Note: auth is implied by selected_features because auth_providers is
    # non-empty, but social is also implied by Google provider.  The key is
    # that jwt gets auto-included even though it's not in the wizard checkboxes.

    resolved = order_features(ctx.features)
    assert "jwt" in resolved
    assert "auth" in resolved
    assert "social" in resolved
    assert resolved.index("jwt") < resolved.index("auth") < resolved.index("social")


def test_email_settings_use_config_not_hardcoded(django_framework):
    """EMAIL settings in base.py should use decouple.config(), not literals."""
    target = _project_dir("email-config-test")
    _cleanup(target)
    cfg = default_config("email-config-test")
    cfg.framework = Framework.DJANGO
    ctx = build_context(cfg, base_dir=target.parent)
    django_framework.scaffold(ctx)

    # Wire auth to inject the email block
    django_framework.wire(ctx)

    settings = ctx.project_dir / "config" / "settings" / "base.py"
    content = settings.read_text()

    # Every email setting should use config(...), not a bare literal
    assert 'config("EMAIL_BACKEND"' in content
    assert 'config("EMAIL_HOST"' in content
    assert 'config("EMAIL_PORT"' in content
    assert 'config("EMAIL_HOST_USER"' in content
    assert 'config("EMAIL_HOST_PASSWORD"' in content
    assert 'config("EMAIL_USE_TLS"' in content
    assert 'config("DEFAULT_FROM_EMAIL"' in content
    assert 'config("SITE_NAME"' in content
    assert 'config("FRONTEND_URL"' in content
    assert "django.core.mail.backends.console.EmailBackend" in content
    _cleanup(target)
