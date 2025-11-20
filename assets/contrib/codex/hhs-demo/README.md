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

## Interactive tutorial (show, then try)

The demo is designed as a guided tour. The layout keeps the checklist on the left and details on the right when there is enough terminal width.

### 1) Watch the navigation example

Start the program and mirror these steps before experimenting on your own:

1. Launch the tour: `go run .`
2. Press <kbd>↓</kbd> or <kbd>j</kbd> to move the cursor down the list.
3. Press <kbd>↑</kbd> or <kbd>k</kbd> to move back up.
4. Hit <kbd>Enter</kbd> (or <kbd>Space</kbd>) to toggle the highlighted topic from `[ ]` to `[✓]`.
5. Observe the **Progress** counter updating and the detail panel showing tips for the current topic.
6. Press <kbd>r</kbd> to reset all items, then <kbd>q</kbd> to exit.

### 2) Try it yourself

Run the same sequence, but explore freely:

- Toggle items in any order to track completion.
- Use the detail panel as a quick refresher on what each topic covers.
- Restart with <kbd>r</kbd> whenever you want a fresh checklist.

### 3) Suggested learning flow

- Start with the introductory topics (first few rows) to understand HomeSetup’s goals.
- Move into aliases and integrations to see how the environment is extended.
- Finish with the plug-ins and ASK/FIREBASE/HSPM sections to explore real workflows.

### Helpful key map (always visible)

```
↑/k   move up        enter/space   toggle complete
↓/j   move down      r             reset progress
q     quit
```
