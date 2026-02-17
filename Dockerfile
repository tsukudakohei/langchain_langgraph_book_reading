# syntax=docker/dockerfile:1.6

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
    && rm -rf /var/lib/apt/lists/*

ARG USER=app
ARG UID=1000
ARG GID=1000

RUN set -eux; \
    if getent group "${GID}" >/dev/null; then \
        EXISTING_GROUP="$(getent group "${GID}" | cut -d: -f1)"; \
    else \
        groupadd -g "${GID}" "${USER}"; \
        EXISTING_GROUP="${USER}"; \
    fi; \
    useradd -m -u "${UID}" -g "${EXISTING_GROUP}" -s /bin/bash "${USER}"

WORKDIR /workspace

COPY requirements.txt /tmp/requirements.txt

RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir \
      "openai==2.16.0" \
      "python-dotenv>=1.0.0" \
      "rich>=13.0.0" \
 && pip install --no-cache-dir -r /tmp/requirements.txt

ARG INSTALL_JUPYTER=0
RUN if [ "${INSTALL_JUPYTER}" = "1" ]; then \
      pip install --no-cache-dir "jupyterlab>=4" "ipykernel>=6"; \
    fi

USER ${USER}
CMD ["bash"]
