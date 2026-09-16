#!/usr/bin/env python3
"""Delete only temporary audio files created inside an episode's .work folder."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_dir", type=Path)
    args = parser.parse_args()
    work = (args.episode_dir / ".work").resolve()
    if not work.is_dir():
        raise SystemExit("找不到单集 .work 目录")
    removed = []
    for path in work.iterdir():
        if path.is_file() and (path.name.startswith("audio.") or path.name == "audio-16k.wav"):
            path.unlink()
            removed.append(str(path))
    print("\n".join(removed) if removed else "没有临时音频需要删除")


if __name__ == "__main__":
    main()
