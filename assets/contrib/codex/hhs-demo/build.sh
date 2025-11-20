#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$ROOT_DIR/bin"
mkdir -p "$BIN_DIR"

platforms=(
  "linux amd32 386"
  "darwin intel32 386"
)

for entry in "${platforms[@]}"; do
  read -r os label goarch <<<"$entry"
  out="$BIN_DIR/hhs-demo-${os}-${label}"
  echo "Building $out"
  GOOS="$os" GOARCH="$goarch" go build -o "$out" ./...
done
