# Pinned official Apache Superset LTS base
ARG SUPERSET_VERSION=6.1.0
ARG SUPERSET_PINNED_VARIANT=-py312
ARG SUPERSET_PINNED_DIGEST=sha256:477b16cf3c28bf573e6686605564bf1c680b5febac50c036d49566f5e59c4ca9

FROM apache/superset:${SUPERSET_VERSION}${SUPERSET_PINNED_VARIANT}@${SUPERSET_PINNED_DIGEST}

USER root

# 1. Apply OS security patches
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y --no-install-recommends \
      -o Dpkg::Options::=--force-confold \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 2. Designated dependency slot: installs overlay/requirements-local.txt into /app/.venv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
COPY overlay/requirements-local.txt /app/requirements-local.txt
RUN if [ -s /app/requirements-local.txt ]; then \
      uv pip install --no-cache --python /app/.venv/bin/python -r /app/requirements-local.txt; \
    fi

# 3. Bake bootstrap scripts into image
COPY docker/ /app/docker/
RUN chmod +x /app/docker/*.sh

# 4. Copy overlay configuration and modular custom package slot onto PYTHONPATH
COPY overlay/custom /app/pythonpath/custom
COPY overlay/superset_config.py /app/pythonpath/superset_config.py
ENV SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py

# Drop privileges back to standard superset user
USER superset
