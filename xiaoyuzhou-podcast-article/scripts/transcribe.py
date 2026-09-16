#!/usr/bin/env python3
"""Transcribe locally with faster-whisper small or base."""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def media_duration(path: Path):
    if not shutil.which("ffprobe"):
        return None
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"ffprobe 无法读取音频：{result.stderr.strip()}")
    return float(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--model", choices=("small", "base"), default="small")
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--cpu-threads", type=int, default=4)
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"音频不存在：{args.input}")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("未安装 faster-whisper；请先安装 requirements.txt")

    duration = media_duration(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    model_ref = str(args.model_path) if args.model_path else args.model
    try:
        model = WhisperModel(model_ref, device="cpu", compute_type="int8", cpu_threads=args.cpu_threads)
        segments, info = model.transcribe(
            str(args.input), language=args.language, beam_size=3, vad_filter=True,
            condition_on_previous_text=False, initial_prompt=args.prompt or None,
        )
        rows = []
        for index, segment in enumerate(segments, 1):
            rows.append({"id": index, "start": segment.start, "end": segment.end, "text": segment.text.strip()})
            if index % 100 == 0:
                print(f"已转写 {index} 段，位置 {segment.end:.1f} 秒", flush=True)
    except Exception as exc:
        hint = "；若属于设备资源不足，可明确改用 --model base" if args.model == "small" else ""
        raise RuntimeError(f"{args.model} 转写失败：{exc}{hint}") from exc

    result = {
        "text": "".join(row["text"] for row in rows), "segments": rows,
        "elapsed_seconds": time.monotonic() - started, "model": args.model,
        "model_reference": model_ref, "language": info.language,
        "duration": duration or (rows[-1]["end"] if rows else 0), "source": "local_whisper",
    }
    (args.output_dir / "transcript.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"[{row['start']:.2f}–{row['end']:.2f}] {row['text']}" for row in rows]
    (args.output_dir / "transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"完成：{len(rows)} 段，耗时 {result['elapsed_seconds']:.1f} 秒，模型 {args.model}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
