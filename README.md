# Apache Superset — Zero-Fork Overlay Architecture

Production-ready Apache Superset deployment scaffolding built on the **Zero-Fork Overlay Pattern**.

---

## 1. Architectural Overview

This repository decouples upstream Apache Superset from local configurations and extensions:

* **Immutable Upstream Engine:** Runs the official `apache/superset` LTS container pinned by tag and SHA256 digest (`6.1.0-py312@sha256:477b16cf3c28bf573e6686605564bf1c680b5febac50c036d49566f5e59c4ca9`). Upstream code is never forked, cloned, or patched.
* **Master Overlay Configuration:** All configurations pass through `overlay/superset_config.py`, mounted at `/app/pythonpath/superset_config.py`.
* **Zero Customizations Out-of-the-Box:** Boots into 100% vanilla Superset by default.
* **Flag- & Environment-Gated Extensibility:** Future extensions, security managers, and connectors are enabled strictly via environment variables.
* **Isolated Modular Python Namespace:** Any future custom Python code resides in `overlay/custom/` on the `PYTHONPATH`.
* **Dedicated Dependency Expansion Slot:** Extra Python dependencies are declared in `overlay/requirements-local.txt` and installed via `uv` into `/app/.venv` during build time.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            IMMUTABLE BASE RUNTIME                                │
│              Official Docker Image: apache/superset:<version>-py312              │
│              - Pinned by exact version and cryptographic multi-arch digest       │
│              - Contains pre-packaged Superset engine and virtual environment     │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ Built via Dockerfile
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             OVERLAY EXTENSION SLOTS                              │
│                                                                                  │
│   overlay/superset_config.py       Master configuration entrypoint               │
│                                    - Placed at /app/pythonpath/superset_config.py│
│                                    - Evaluates environment variables & flags     │
│                                                                                  │
│   overlay/requirements-local.txt   Dedicated dependency expansion slot           │
│                                    - Installed via uv into /app/.venv            │
│                                    - Initially empty                             │
│                                                                                  │
│   overlay/custom/                  Isolated Python package namespace             │
│                                    - Placed at /app/pythonpath/custom            │
│                                    - Designated slot for future modular code     │
│                                                                                  │
│   docker/superset-init.sh          Idempotent database and role bootstrap        │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ Managed via Docker Compose
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          ENVIRONMENT-DRIVEN POSTURES                             │
│                                                                                  │
│   POSTURE A: Local Development     │   POSTURE B: Production (Cloud / EC2 / ECS) │
│   - docker-compose.local.yml       │   - docker-compose.prod.yml                 │
│   - Containerized PostgreSQL & Redis│   - External Managed PostgreSQL & Redis     │
│   - Local .env file                │   - Resource limits, log rotation, TLS proxy │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
├── .dockerignore
├── .gitignore
├── .env.example
├── Dockerfile
├── docker-compose.yml           # Base shared services (Redis, web, Celery worker, beat, init)
├── docker-compose.local.yml     # Local dev overlay (containerized PostgreSQL metadata DB)
├── docker-compose.prod.yml      # Production cloud overlay (external DB, resource caps)
├── docker/
│   └── superset-init.sh        # Idempotent DB migration and role sync script
└── overlay/
    ├── requirements-local.txt   # Extra pip packages (starts empty)
    ├── superset_config.py       # Master config entrypoint (reads from environment)
    └── custom/
        └── __init__.py          # Python namespace package for future modules
```

---

## 3. Quickstart (Local Development)

### 3.1. Initialize Environment Variables
Create your local `.env` from `.env.example` and generate a cryptographically strong `SUPERSET_SECRET_KEY`:

```bash
cp .env.example .env
# Set SUPERSET_SECRET_KEY in .env using:
openssl rand -base64 42
```

### 3.2. Build and Boot Stack
Run the local posture (combining base services with the containerized Postgres database):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

### 3.3. Check Initialization and Health
Check service health and bootstrap progress:

```bash
# View initialization logs
docker compose -f docker-compose.yml -f docker-compose.local.yml logs -f superset-init

# Check service status
docker compose -f docker-compose.yml -f docker-compose.local.yml ps

# Verify endpoint responds
curl http://localhost:8088/health
```

Access Superset in your browser at `http://localhost:8088` with the credentials specified in `.env`:
* **Username:** `admin` (or value of `ADMIN_USERNAME`)
* **Password:** `admin` (or value of `ADMIN_PASSWORD`)

---

## 4. Production Deployment Posture

For cloud deployments (AWS ECS, EC2, Kubernetes, or Bare Metal) using external managed services (e.g., AWS RDS PostgreSQL, AWS ElastiCache Redis):

1. Populate `prod.env` with external connection details:
   * `DATABASE_URL` or `DATABASE_HOST`/`DATABASE_PORT`/`DATABASE_USER`/`DATABASE_PASSWORD`/`DATABASE_DB`
   * `REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD`
   * `SUPERSET_SECRET_KEY`
   * `ENABLE_PROXY_FIX=true`
   * `SESSION_COOKIE_SECURE=true`
   * `PREFERRED_URL_SCHEME=https`
   * `FORCE_HTTPS=true`

2. Deploy using the production overlay:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

---

## 5. Architectural Rules for Extending this Project

1. **Feature Flag & Environment Variable Gating:**
   * No customization must be active by default.
   * Parse toggles with helper functions (e.g. `_env_bool("ENABLE_FEATURE", "false")`).
2. **Subclass and Spread, Never Clobber:**
   * Always spread base configurations (e.g., `DEFAULT_FEATURE_FLAGS`, `STOCK_TALISMAN_CONFIG`). Never overwrite composite dictionaries wholesale.
3. **Clean Separation of Configuration and Logic:**
   * `overlay/superset_config.py` should only handle declarative settings and flag evaluation.
   * Place Python classes, custom security managers, API endpoints, or database hooks under `overlay/custom/<module>.py` and import them conditionally.
4. **Isolated Dependency Management:**
   * Place any additional pip dependencies into `overlay/requirements-local.txt`. They will be installed into `/app/.venv` at image build time via `uv`.
