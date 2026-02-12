#!/bin/sh
set -eu

cd "$(dirname "$0")"

uid="$(id -u)"
gid="$(id -g)"

set -- docker compose run --rm

if [ "${DRY_RUN:-}" = "1" ]; then
  set -- "$@" -e DRY_RUN=1
fi
if [ -n "${OPENAI_MODEL:-}" ]; then
  set -- "$@" -e OPENAI_MODEL="$OPENAI_MODEL"
fi

set -- "$@" study python docker-check/4-2.py

exec env UID="$uid" GID="$gid" "$@"

