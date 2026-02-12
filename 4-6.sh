#!/bin/sh
set -eu

cd "$(dirname "$0")"

uid="$(id -u)"
gid="$(id -g)"

set -- docker compose run --rm

if [ "${SERVE:-}" = "1" ]; then
  set -- "$@" --service-ports
fi
if [ "${DRY_RUN:-}" = "1" ]; then
  set -- "$@" -e DRY_RUN=1
fi
if [ -n "${OPENAI_MODEL:-}" ]; then
  set -- "$@" -e OPENAI_MODEL="$OPENAI_MODEL"
fi

if [ "${SERVE:-}" = "1" ]; then
  set -- "$@" study python docker-check/4-6.py --serve --host 0.0.0.0 --port 8000
else
  set -- "$@" study python docker-check/4-6.py
fi

exec env UID="$uid" GID="$gid" "$@"

