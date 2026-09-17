#!/usr/bin/env python3
"""Check the cloud-transcription prerequisites without revealing the API key."""

import json
import os
import platform
import shlex
import sys
from pathlib import Path


def setting(name):
    if os.environ.get(name):
        return os.environ[name]
    path = Path.home() / ".config" / "xiaoyuzhou-podcast-article" / "env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                values = shlex.split(line.split("=", 1)[1])
                return values[0] if values else ""
    return ""


def main():
    result = {
        "python": {"version": platform.python_version(), "supported": sys.version_info >= (3, 9)},
        "system": platform.system(),
        "dashscope_api_key_configured": bool(setting("DASHSCOPE_API_KEY").strip()),
        "free_tier_stop_confirmed": setting("DASHSCOPE_FREE_TIER_STOP_CONFIRMED") == "1",
        "region": "cn-beijing",
        "workspace_endpoint_configured": bool(setting("DASHSCOPE_BASE_URL")),
        "model": "paraformer-v2",
    }
    result["ready"] = bool(
        result["python"]["supported"]
        and result["dashscope_api_key_configured"]
        and result["free_tier_stop_confirmed"]
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()
