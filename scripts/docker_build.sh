#!/usr/bin/env bash
# docker_build.sh — Build and optionally run the O.D.I.A. production Docker image.
#
# Usage:
#   bash scripts/docker_build.sh            # Build image tagged odia:latest
#   bash scripts/docker_build.sh --run      # Build and start the container
#   bash scripts/docker_build.sh --push     # Build and push to Docker Hub (requires login)
#
# Options:
#   --tag <name>   Custom image tag (default: odia:latest)
#   --run          Run the container after building
#   --push         Push image after building
#   --no-cache     Force a clean build (no layer cache)

set -euo pipefail

IMAGE="odia:latest"
DO_RUN=false
DO_PUSH=false
NO_CACHE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)    IMAGE="$2"; shift 2 ;;
        --run)    DO_RUN=true; shift ;;
        --push)   DO_PUSH=true; shift ;;
        --no-cache) NO_CACHE="--no-cache"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=============================================="
echo "  O.D.I.A. Docker Build"
echo "=============================================="
echo "  Image : $IMAGE"
echo "  Root  : $REPO_ROOT"
echo ""

# Build
docker build $NO_CACHE -t "$IMAGE" "$REPO_ROOT"
echo ""
echo "[OK] Build complete: $IMAGE"

# Size report
SIZE=$(docker image inspect "$IMAGE" --format='{{.Size}}' | awk '{printf "%.0f MB", $1/1024/1024}')
echo "     Image size: $SIZE"
echo ""

# Push
if [ "$DO_PUSH" = true ]; then
    echo "Pushing $IMAGE ..."
    docker push "$IMAGE"
    echo "[OK] Push complete."
fi

# Run
if [ "$DO_RUN" = true ]; then
    echo "Starting container ..."
    echo "  API + frontend available at http://localhost:8080"
    echo "  Press Ctrl+C to stop."
    echo ""
    docker run --rm -it \
        -p 8080:8080 \
        -v odia-data:/data \
        -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
        -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
        "$IMAGE"
fi
