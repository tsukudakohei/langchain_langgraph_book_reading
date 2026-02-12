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

RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir \
      "openai==2.20.0" \
      "openai-agents==0.8.1" \
      "python-dotenv==1.2.1" \
      "rich==14.3.2" \
      "langchain==1.2.10" \
      "langchain-core==1.2.11" \
      "langchain-openai==1.1.9" \
      "langgraph==1.0.8" \
      "langgraph-prebuilt==1.0.7"

ARG INSTALL_JUPYTER=0
RUN if [ "${INSTALL_JUPYTER}" = "1" ]; then \
      pip install --no-cache-dir "jupyterlab>=4" "ipykernel>=6"; \
    fi

USER ${USER}
CMD ["bash"]
