#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/third_party/llama.cpp"
PIN="961c376a2daa42220ec09663b9bde32c5fba1f70"
if [ ! -d "$SOURCE/.git" ]; then
  mkdir -p "$(dirname "$SOURCE")"
  git clone https://github.com/ggml-org/llama.cpp.git "$SOURCE"
fi
git -C "$SOURCE" fetch --depth 1 origin "$PIN"
git -C "$SOURCE" checkout --detach "$PIN"
echo "llama.cpp pinned to $(git -C "$SOURCE" rev-parse HEAD)"
