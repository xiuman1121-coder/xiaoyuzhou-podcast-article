#!/usr/bin/env python3
"""Safely save the user's Alibaba Model Studio API key outside the Skill."""

import getpass
import shlex
from pathlib import Path


def main():
    print("即将进入隐藏输入。下一行提示出现后再粘贴 API Key；输入时屏幕不会显示字符。")
    key = getpass.getpass("API Key（隐藏输入）：").strip()
    if not key.startswith("sk-") or len(key) < 20 or key.count("sk-") != 1:
        raise SystemExit("输入不像有效的百炼 API Key，配置未保存。")
    config_dir = Path.home() / ".config" / "xiaoyuzhou-podcast-article"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_dir.chmod(0o700)
    config_file = config_dir / "env"
    endpoint = input(
        "粘贴 API Key 页面显示的 OpenAI Compatible URL，然后按回车："
    ).strip()
    suffix = "/compatible-mode/v1"
    if not endpoint.startswith("https://") or not endpoint.endswith(suffix):
        raise SystemExit("业务空间 URL 格式不正确，配置未保存。")
    base_url = endpoint[:-len(suffix)] + "/api/v1"
    config_file.write_text(
        f"DASHSCOPE_API_KEY={shlex.quote(key)}\n"
        f"DASHSCOPE_BASE_URL={shlex.quote(base_url)}\n"
        "DASHSCOPE_FREE_TIER_STOP_CONFIRMED=1\n",
        encoding="utf-8",
    )
    config_file.chmod(0o600)
    print("配置成功：API Key 已保存到个人配置目录，未显示完整内容。")


if __name__ == "__main__":
    main()
