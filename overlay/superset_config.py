"""
Master Apache Superset Configuration Entrypoint
Zero customizations active by default. Vanilla Superset behavior.
All future configurations and optimizations are driven via environment variables and feature flags.
"""
import os
import logging
from superset.config import (
    DEFAULT_FEATURE_FLAGS,
    TALISMAN_CONFIG as STOCK_TALISMAN_CONFIG,
)

logger = logging.getLogger("superset.overlay")

def _env_bool(name: str, default: str = "false") -> bool:
    """Helper to parse boolean values from environment variables."""
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")

# ---------------------------------------------------------------------------
# 1. Security & Core Secrets
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

# ---------------------------------------------------------------------------
# 2. Metadata Database Connection
# ---------------------------------------------------------------------------
# Accepts a full connection URI or individual component variables
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
    "postgresql+psycopg2://"
    f"{os.environ.get('DATABASE_USER', 'superset')}:{os.environ.get('DATABASE_PASSWORD', 'superset')}"
    f"@{os.environ.get('DATABASE_HOST', 'db')}:{os.environ.get('DATABASE_PORT', '5432')}"
    f"/{os.environ.get('DATABASE_DB', 'superset')}"
)

SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": int(os.environ.get("SQLALCHEMY_POOL_RECYCLE", "300")),
    "pool_size": int(os.environ.get("METADATA_POOL_SIZE", "5")),
    "max_overflow": int(os.environ.get("METADATA_POOL_MAX_OVERFLOW", "5")),
}

# ---------------------------------------------------------------------------
# 3. Cache & Celery Asynchronous Execution
# ---------------------------------------------------------------------------
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
REDIS_AUTH = f":{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""

# Discrete logical database indexes in Redis
REDIS_CELERY_DB = os.environ.get("REDIS_CELERY_DB", "0")
REDIS_RESULTS_DB = os.environ.get("REDIS_RESULTS_DB", "1")
REDIS_CACHE_DB = os.environ.get("REDIS_CACHE_DB", "2")

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "86400")),
    "CACHE_KEY_PREFIX": "superset_cache_",
    "CACHE_REDIS_URL": f"redis://{REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/{REDIS_CACHE_DB}",
}
DATA_CACHE_CONFIG = CACHE_CONFIG

class CeleryConfig:
    broker_url = f"redis://{REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    result_backend = f"redis://{REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    task_track_started = True
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    imports = ("superset.tasks", "superset.tasks.cache")

CELERY_CONFIG = CeleryConfig

# ---------------------------------------------------------------------------
# 4. Feature Flags (Extended Dynamically)
# ---------------------------------------------------------------------------
# Stock feature flags extended with standard environment toggles
FEATURE_FLAGS = {
    **DEFAULT_FEATURE_FLAGS,
    "ENABLE_TEMPLATE_PROCESSING": _env_bool("ENABLE_TEMPLATE_PROCESSING", "true"),
    "DASHBOARD_CROSS_FILTERS": _env_bool("DASHBOARD_CROSS_FILTERS", "true"),
}

# ---------------------------------------------------------------------------
# 5. Network & Reverse Proxy Settings
# ---------------------------------------------------------------------------
ENABLE_PROXY_FIX = _env_bool("ENABLE_PROXY_FIX", "false")
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", "false")
PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "http")

TALISMAN_CONFIG = {
    **STOCK_TALISMAN_CONFIG,
    "force_https": _env_bool("FORCE_HTTPS", "false"),
}

# ---------------------------------------------------------------------------
# 6. Extensibility Pattern: Environment-Driven Configuration Hooks
# ---------------------------------------------------------------------------
# Any future feature, optimization, or integration must be gated by a condition
# checking an environment variable or feature flag before modifying runtime state.
#
# Pattern Example:
# if _env_bool("ENABLE_MY_CUSTOM_FEATURE", "false"):
#     # Apply feature flag or import modular logic from `custom.<module>`
#     FEATURE_FLAGS["MY_CUSTOM_FEATURE"] = True
