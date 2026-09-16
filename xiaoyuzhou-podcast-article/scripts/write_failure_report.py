#!/usr/bin/env python3
"""Create a clear failure report instead of a fabricated article."""

import argparse
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_dir", type=Path)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--missing", default="未知")
    parser.add_argument("--attempt", action="append", default=[])
    args = parser.parse_args()
    lines = [
        "# 处理失败报告", "", f"- 时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 失败阶段：{args.stage}", f"- 失败原因：{args.reason}", f"- 缺失或不可靠范围：{args.missing}",
        "", "## 已尝试", "",
    ]
    lines.extend(f"- {item}" for item in (args.attempt or ["尚未记录重试动作"]))
    lines += ["", "本次未生成正式 HTML，以免用推测补齐缺失内容。", ""]
    path = args.episode_dir / "failure-report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
