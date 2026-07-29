#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 0 && "${1:-}" != "--docker" ]]; then
  printf '%s\n' "Usage: ./run.sh" >&2
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  printf '%s\n' "Docker is not installed. Install Docker Desktop from https://docs.docker.com/desktop/install/mac-install/" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  if [[ "$(uname -s)" == "Darwin" ]]; then
    printf '%s\n' "Docker is installed but not running; starting Docker Desktop..."
    open -a Docker >/dev/null 2>&1 &
  else
    printf '%s\n' "Docker is installed but the daemon is not running. Start it and retry." >&2
    exit 1
  fi

  timeout_seconds="${TEA_DOCKER_START_TIMEOUT:-120}"
  for ((second = 0; second < timeout_seconds; second++)); do
    if docker info >/dev/null 2>&1; then
      printf '%s\n' "Docker daemon is ready."
      break
    fi
    if (( second > 0 && second % 5 == 0 )); then
      printf '%s\n' "Still waiting for Docker Desktop (${second}/${timeout_seconds}s)..."
    fi
    sleep 1
  done
  if ! docker info >/dev/null 2>&1; then
    printf '%s\n' "Docker Desktop did not become ready within ${timeout_seconds}s." >&2
    exit 1
  fi
fi

if [[ -n "${DOCKER_PLATFORM:-}" ]]; then
  docker build --platform "$DOCKER_PLATFORM" -f Dockerfile.jekyll -t tea-docs .
  printf '%s\n' "Preview: http://localhost:4000/tea/docs/home/"
  if [[ "${TEA_OPEN_BROWSER:-1}" == "1" && "$(uname -s)" == "Darwin" ]]; then
    open "http://localhost:4000/tea/docs/home/" >/dev/null 2>&1 &
  fi
  exec docker run --rm --platform "$DOCKER_PLATFORM" \
    -p 4000:4000 \
    -p 35729:35729 \
    -v "$PWD:/srv/jekyll" \
    tea-docs
fi

docker build -f Dockerfile.jekyll -t tea-docs .
printf '%s\n' "Preview: http://localhost:4000/tea/docs/home/"
if [[ "${TEA_OPEN_BROWSER:-1}" == "1" && "$(uname -s)" == "Darwin" ]]; then
  open "http://localhost:4000/tea/docs/home/" >/dev/null 2>&1 &
fi
exec docker run --rm \
  -p 4000:4000 \
  -p 35729:35729 \
  -v "$PWD:/srv/jekyll" \
  tea-docs
