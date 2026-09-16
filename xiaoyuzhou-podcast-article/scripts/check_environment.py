#!/usr/bin/env python3
"""Report whether the local desktop environment can run the workflow."""

import importlib.util
import json
import platform
import shutil
import sys


def main():
    result = {
        "python": {"version": platform.python_version(), "supported": sys.version_info >= (3, 9)},
        "system": platform.system(),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "faster_whisper": importlib.util.find_spec("faster_whisper") is not None,
    }
    result["media_diagnostics_ready"] = bool(result["ffmpeg"] and result["ffprobe"])
    result["ready"] = bool(result["python"]["supported"] and result["faster_whisper"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()
