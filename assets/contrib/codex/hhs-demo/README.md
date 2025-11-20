# HomeSetup Hands-on Demo

An interactive Bubble Tea + Lip Gloss terminal checklist that walks through the key HomeSetup topics outlined in `assets/devel/hhs-demo-topics.md`. Use the keyboard to browse topics, mark them complete, and restart the tour at any time.

## Running locally

```bash
go run .
```

## Building binaries

Use the provided build script to generate Linux and macOS binaries under `bin/`.

```bash
./build.sh
```

The script currently targets `linux/amd64` and `darwin/arm64`. Adjust the matrices in `build.sh` if you need other architectures.
