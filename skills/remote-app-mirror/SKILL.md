---
name: remote-app-mirror
description: Mirror and interact with a running app window through a browser. Use when someone wants to view and control an app remotely.
---

# Remote app mirror

Mirror one running app window to a browser. The bundled bridge captures the selected window and forwards supported browser input to it. It does not start or modify the app.

## Workflow

1. Identify the running app window the user wants to mirror. Use the bundled window list when needed; if the match is ambiguous, ask which window to use.
2. Run the skill launcher at `scripts/mirror.py`. It invokes the shared program in `programs/remote-app-mirror/`. Do not launch another copy of the app.
3. Give the user the URL printed by the bridge. Browser taps, text, and scroll input are forwarded to the app. On touch devices, pinch zooms and one-finger drag pans; taps map through the zoom and pan transform to the correct app coordinates.

## Start the bridge

From the `ai-skills` repository root, use the skill launcher:

```sh
python3 "skills/remote-app-mirror/scripts/mirror.py" --list-windows
python3 "skills/remote-app-mirror/scripts/mirror.py" --window-title "part of the unique window title"
```

The bridge prints the URL for the mirrored app. Use `--port` to choose another port. Read [bridge limitations](references/bridge-limitations.md) when needed.
