#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$ROOT_DIR/bin"
mkdir -p "$BIN_DIR"

platforms=(
  "linux amd64"
  "darwin arm64"
)

for entry in "${platforms[@]}"; do
  read -r os arch <<<"$entry"
  out="$BIN_DIR/hhs-demo-${os}-${arch}"
  echo "Building $out"
  GOOS="$os" GOARCH="$arch" go build -o "$out" ./...
done
