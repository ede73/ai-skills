# Bridge limitations

- The bridge captures one application window. It does not mirror other windows or the full desktop.
- Browser taps map through the current zoom and pan transform to normalized coordinates in the selected window. Browser drag pans the image; it does not drag controls inside the app. Pinch zoom is limited to 1×–6×, and pan stays bounded so part of the image remains visible.
- Moving or resizing the app window during a session can make input coordinates stale. Restart the bridge after moving or resizing the window.
- Text is forwarded as Unicode keystrokes. IME composition, secure input fields, global shortcuts, clipboard transfer, file dialogs, and multi-window workflows are not guaranteed; use the app locally for those cases.
