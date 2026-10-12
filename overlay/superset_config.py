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
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "5/lEyE2pXgbPXWDUAP1DpcrVIs2jKTf8txUlhj9lV9mhyd6Zc4O9b15g")

# Prevent client browsers from caching dynamic file exports (ZIP bundles)
SEND_FILE_MAX_AGE_DEFAULT = 0

def FLASK_APP_MUTATOR(app):
    from flask import request

    @app.after_request
    def force_no_cache_on_exports(response):
        if "/export/" in request.path:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

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
# 6. Design System & Corporate Theming (Subisu Cablenet)
# ---------------------------------------------------------------------------
# Authenticated against official Subisu brand identity (subisu.net.np):
# Primary Brand: #1D479B (Subisu Cobalt Blue - .component-tile-primary / .su-text-primary)
# Secondary Brand: #C12161 (Subisu Crimson Berry - .component-tile-secondary / .su-text-secondary)
# Signature Gradient: linear-gradient(90deg, #1D479B, #C12161)
# ---------------------------------------------------------------------------

THEME_DEFAULT = {
    "token": {
        # Core Brand Palette (Subisu Official Website Colors)
        "colorPrimary": "#1D479B",          # Subisu Primary Cobalt Blue
        "colorPrimaryHover": "#2A5FBF",
        "colorPrimaryActive": "#143270",
        "colorPrimaryBg": "#EEF3FA",        # Subtle brand tint
        "colorPrimaryBorder": "#BDD1F2",

        # Semantic Status Tokens
        "colorSuccess": "#28A745",          # Active / Renewals / Upgrades
        "colorSuccessBg": "#EAF7ED",
        "colorError": "#DC3545",            # Churn / Downgrade / Drop
        "colorErrorBg": "#FDF2F2",
        "colorWarning": "#F59E0B",          # Expiring / Threshold
        "colorWarningBg": "#FFFBEB",
        "colorInfo": "#17A2B8",             # Broadband info / Cyan
        "colorInfoBg": "#EDF9FA",

        # Neutral & Background Hierarchy
        "colorBgBase": "#FFFFFF",
        "colorBgLayout": "#F8F9FA",        # Clean enterprise surface
        "colorBgContainer": "#FFFFFF",
        "colorBgElevated": "#FFFFFF",
        "colorBorder": "#E2E8F0",          # 1px crisp borders
        "colorBorderSecondary": "#F1F5F9",

        # Typography Hierarchy
        "colorText": "#0C0C0C",            # Subisu .su-text-black
        "colorTextSecondary": "#495057",   # Subisu slate secondary
        "colorTextTertiary": "#6C757D",    # Subisu muted caption
        "colorTextQuaternary": "#CED4DA",
        "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "fontSize": 13,
        "fontSizeHeading1": 24,
        "fontSizeHeading2": 20,
        "fontSizeHeading3": 16,
        "fontSizeHeading4": 14,

        # Geometry & Spacing (8px Grid, 12px Radius)
        "borderRadius": 8,
        "borderRadiusLG": 12,
        "borderRadiusSM": 6,
        "boxShadow": "0 1px 3px 0 rgba(12, 12, 12, 0.05), 0 1px 2px -1px rgba(12, 12, 12, 0.05)",
        "boxShadowSecondary": "0 4px 6px -1px rgba(12, 12, 12, 0.07), 0 2px 4px -2px rgba(12, 12, 12, 0.05)",
        "wireframe": False,
    },
    "components": {
        "Tabs": {
            "cardBg": "#FFFFFF",
            "horizontalItemPadding": "10px 16px",
            "itemSelectedColor": "#1D479B",
            "itemHoverColor": "#2A5FBF",
            "inkBarColor": "#1D479B",
            "titleFontSize": 13,
            "horizontalMargin": "0 0 16px 0",
        },
        "Table": {
            "headerBg": "#F8F9FA",
            "headerColor": "#495057",
            "headerSplitColor": "transparent",
            "rowHoverBg": "#F1F5F9",
            "borderColor": "#E2E8F0",
            "fontSize": 12,
            "cellPaddingBlock": 8,
            "cellPaddingInline": 12,
        },
        "Button": {
            "borderRadius": 8,
            "controlHeight": 34,
            "fontWeight": 600,
        },
        "Select": {
            "controlHeight": 34,
            "borderRadius": 8,
            "colorBorder": "#CED4DA",
        },
        "Card": {
            "borderRadiusLG": 12,
            "headerBg": "#FFFFFF",
            "headerFontSize": 14,
            "colorBorderSecondary": "#E2E8F0",
        },
    },
}

# Corporate Chart Color Palettes (Derived directly from Subisu brand architecture)
EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {
        "id": "subisu_brand_categorical",
        "description": "Subisu Cabelenet Official Brand Palette (Cobalt Blue & Crimson Berry)",
        "label": "Subisu Enterprise Categorical",
        "isDefault": True,
        "colors": [
            "#1D479B",  # 1. Subisu Cobalt Blue (Primary brand)
            "#C12161",  # 2. Subisu Crimson Berry (Secondary brand)
            "#007BFF",  # 3. Subisu Sky Blue (Digital services)
            "#28A745",  # 4. Success Green (Renewals / Active)
            "#FD7E14",  # 5. ClearTV Orange (Digital TV / Entertainment)
            "#17A2B8",  # 6. Broadband Teal/Cyan (FTTH Internet)
            "#6F42C1",  # 7. Enterprise Purple (SME & Corporate)
            "#FFC107",  # 8. Amber Gold (Expiring / Notice)
            "#E83E8C",  # 9. Vibrant Pink (Promotions & Value packs)
            "#6C757D",  # 10. Slate Neutral (Others / Unclassified)
        ],
    }
]

EXTRA_SEQUENTIAL_COLOR_SCHEMES = [
    {
        "id": "subisu_blue_sequential",
        "description": "Subisu Official Cobalt Blue Sequential for volume & ARPU density",
        "label": "Subisu Cobalt Sequential",
        "isDefault": True,
        "isDiverging": False,
        "colors": [
            "#EEF3FA",  # Lightest tint
            "#D8E4F4",
            "#B6CDE9",
            "#8DAFDC",
            "#5D8ECD",
            "#3A72BE",
            "#1D479B",  # Core Subisu Blue
            "#16387D",
            "#10295F",
            "#0A1B40",  # Deepest Midnight Navy
        ],
    },
    {
        "id": "subisu_diverging_delta",
        "description": "Subisu Red-Slate-Green for ARPU growth, revenue shifts & deltas",
        "label": "Subisu Diverging Growth Delta",
        "isDefault": False,
        "isDiverging": True,
        "colors": [
            "#DC3545",  # Negative / Churn (-100%)
            "#F18A94",
            "#FACDCE",
            "#F8F9FA",  # Neutral / Zero change (0.00)
            "#C4E7CB",
            "#63BE7B",
            "#28A745",  # Positive / Upgrade (+100%)
        ],
    },
]

# Instance-wide Default Palette Directives
DEFAULT_CATEGORICAL_COLOR_SCHEME = "subisu_brand_categorical"
DEFAULT_SEQUENTIAL_COLOR_SCHEME = "subisu_blue_sequential"

# ---------------------------------------------------------------------------
# 7. Extensibility Pattern: Environment-Driven Configuration Hooks
# ---------------------------------------------------------------------------
# Any future feature, optimization, or integration must be gated by a condition
# checking an environment variable or feature flag before modifying runtime state.
#
# Pattern Example:
# if _env_bool("ENABLE_MY_CUSTOM_FEATURE", "false"):
#     # Apply feature flag or import modular logic from `custom.<module>`
#     FEATURE_FLAGS["MY_CUSTOM_FEATURE"] = True
