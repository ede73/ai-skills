#!/usr/bin/env python3
"""Launch the shared remote-app-mirror program from the ai-skills repository."""

from __future__ import annotations

import os
import sys
from pathlib import Path


repository_root = Path(__file__).resolve().parents[3]
program = repository_root / "programs" / "remote-app-mirror" / "mirror.py"
if not program.is_file():
    raise SystemExit(f"Shared mirror program was not found: {program}")

os.execv(sys.executable, [sys.executable, str(program), *sys.argv[1:]])
