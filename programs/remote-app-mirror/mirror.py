#!/usr/bin/env python3
"""Single-window macOS LAN mirror. No dependencies beyond Python and macOS tools."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import socket
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROGRAM_ROOT = Path(__file__).resolve().parent
WINDOW_LIST = PROGRAM_ROOT / "scripts" / "window-list.swift"
ACTIVATE_APP = PROGRAM_ROOT / "scripts" / "activate-app.swift"
WEB_ROOT = PROGRAM_ROOT / "web"
HTML_PAGE = WEB_ROOT / "index.html"
STYLESHEET = WEB_ROOT / "mirror.css"
JAVASCRIPT = WEB_ROOT / "mirror.js"


def run_window_list() -> list[dict]:
    result = subprocess.run(["swift", str(WINDOW_LIST)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


class QuartzInput:
    """Small CoreGraphics wrapper for pointer, Unicode key, and scroll events."""

    class Point(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

    def __init__(self):
        app_services = "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        self.cg = ctypes.CDLL(app_services)
        self.cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        self.cg.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, self.Point, ctypes.c_uint32]
        self.cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
        self.cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]
        self.cg.CGEventKeyboardSetUnicodeString.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_uint16)]
        self.cg.CGEventCreateScrollWheelEvent.restype = ctypes.c_void_p
        self.cg.CGEventCreateScrollWheelEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
        self.cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        self.cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self.cf.CFRelease.argtypes = [ctypes.c_void_p]

    def post(self, event):
        if not event:
            raise RuntimeError("macOS did not create an input event; check Accessibility permission")
        self.cg.CGEventPost(0, event)  # kCGHIDEventTap
        self.cf.CFRelease(event)

    def mouse(self, kind: str, x: float, y: float, button: int = 0):
        buttons = {0: (0, 1, 2, 5), 1: (2, 25, 26, 27), 2: (1, 3, 4, 6)}
        quartz_button, left_down, left_up, left_move = buttons.get(button, buttons[0])
        event_type = {"down": left_down, "up": left_up, "move": left_move}[kind]
        self.post(self.cg.CGEventCreateMouseEvent(None, event_type, self.Point(x, y), quartz_button))

    def text(self, value: str):
        utf16 = value.encode("utf-16-le")
        units = (ctypes.c_uint16 * (len(utf16) // 2)).from_buffer_copy(utf16)
        for down in (True, False):
            event = self.cg.CGEventCreateKeyboardEvent(None, 0, down)
            self.cg.CGEventKeyboardSetUnicodeString(event, len(units), units)
            self.post(event)

    def key(self, name: str):
        keycodes = {"backspace": 51, "enter": 36, "tab": 48, "escape": 53, "up": 126, "down": 125, "left": 123, "right": 124, "delete": 117}
        code = keycodes.get(name)
        if code is None:
            return
        for down in (True, False):
            self.post(self.cg.CGEventCreateKeyboardEvent(None, code, down))

    def scroll(self, dx: float, dy: float):
        event = self.cg.CGEventCreateScrollWheelEvent(None, 0, 2, int(-dy / 30), int(-dx / 30), 0)
        self.post(event)


class MirrorHandler(BaseHTTPRequestHandler):
    window: dict
    input: QuartzInput
    lock = threading.Lock()

    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_asset(HTML_PAGE, "text/html; charset=utf-8")
        elif self.path == "/mirror.css":
            self.send_asset(STYLESHEET, "text/css; charset=utf-8")
        elif self.path == "/mirror.js":
            self.send_asset(JAVASCRIPT, "text/javascript; charset=utf-8")
        elif self.path.startswith("/frame.jpg"):
            with self.lock, tempfile.TemporaryDirectory(prefix="mac-window-mirror-") as tmp:
                target = Path(tmp) / "frame.jpg"
                result = subprocess.run(["/usr/sbin/screencapture", "-x", "-o", "-l", str(self.window["id"]), "-t", "jpg", str(target)], capture_output=True)
                if result.returncode or not target.exists():
                    self.send_error(503, "Window capture failed. Grant Screen Recording permission and restart the bridge."); return
                data = target.read_bytes()
            self.send_response(200); self.send_header("Content-Type", "image/jpeg"); self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        else:
            self.send_error(404)

    def send_asset(self, path: Path, content_type: str):
        try:
            data = path.read_bytes()
        except OSError:
            self.send_error(500, f"Could not load mirror asset: {path.name}")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/input":
            self.send_error(404); return
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 65536)
            data = json.loads(self.rfile.read(length))
            kind = data.get("kind")
            nx, ny = float(data.get("x", .5)), float(data.get("y", .5))
            if not 0 <= nx <= 1 or not 0 <= ny <= 1:
                self.send_error(400, "Input must stay inside the selected window."); return
            x = float(self.window["x"]) + nx * float(self.window["width"])
            y = float(self.window["y"]) + ny * float(self.window["height"])
            if kind in ("down", "up", "move"):
                self.input.mouse(kind, x, y, int(data.get("button", 0)))
            elif kind == "scroll":
                self.input.mouse("move", x, y); self.input.scroll(float(data.get("dx", 0)), float(data.get("dy", 0)))
            elif kind == "text":
                self.input.text(str(data.get("text", ""))[:4096])
            elif kind == "key":
                self.input.key(str(data.get("key", "")))
            else:
                self.send_error(400); return
            self.send_response(204); self.end_headers()
        except Exception as exc:
            self.send_error(500, str(exc))


def main():
    parser = argparse.ArgumentParser(description="Mirror one macOS app window to a LAN browser.")
    parser.add_argument("--list-windows", action="store_true", help="list on-screen application windows")
    parser.add_argument("--window-title", help="unique title substring of the target window")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.list_windows:
        for item in run_window_list():
            print(f'{item["id"]:>7}  {item["owner"]}: {item["title"] or "(untitled)"}  {item["width"]:.0f}×{item["height"]:.0f}')
        return
    if not args.window_title:
        parser.error("--window-title is required unless --list-windows is used")
    matches = [w for w in run_window_list() if args.window_title.casefold() in f'{w["owner"]} {w["title"]}'.casefold()]
    if len(matches) != 1:
        raise SystemExit(f"Expected one title match, found {len(matches)}. Run --list-windows and use a more specific title.")
    window = matches[0]
    if window["width"] <= 0 or window["height"] <= 0:
        raise SystemExit("Selected window has invalid bounds")
    subprocess.run(["swift", str(ACTIVATE_APP), str(window["pid"])], check=True, capture_output=True, text=True)
    MirrorHandler.window = window
    MirrorHandler.input = QuartzInput()
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 80))
        lan_ip = probe.getsockname()[0]
    finally:
        probe.close()
    server = ThreadingHTTPServer(("0.0.0.0", args.port), MirrorHandler)
    server.daemon_threads = True
    print(f'Mirroring {window["owner"]}: {window["title"] or "(untitled)"} at http://{lan_ip}:{args.port}', flush=True)
    print("Listening on 0.0.0.0. Anyone able to reach this port can control the selected window. Ctrl-C stops the bridge.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
