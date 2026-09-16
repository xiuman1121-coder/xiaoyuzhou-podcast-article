#!/usr/bin/env python3
"""Check transcript timing and coverage without inventing missing content."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--episode", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.transcript.read_text(encoding="utf-8"))
    segments = data.get("segments") or []
    expected = data.get("duration") or 0
    if args.episode and args.episode.exists():
        expected = json.loads(args.episode.read_text(encoding="utf-8")).get("duration") or expected

    fatal, warnings = [], []
    if not segments or not data.get("text", "").strip():
        fatal.append("逐字稿为空")
    previous_end = 0.0
    long_gaps = []
    repeats = []
    previous_text = None
    repeat_run = 0
    for index, segment in enumerate(segments, 1):
        start, end = float(segment.get("start", -1)), float(segment.get("end", -1))
        if start < 0 or end <= start:
            fatal.append(f"第 {index} 段时间无效")
        if start + 0.5 < previous_end:
            fatal.append(f"第 {index} 段时间倒序")
        gap = start - previous_end
        if gap > 30:
            long_gaps.append({"after_segment": index - 1, "seconds": round(gap, 2)})
        if gap > 180:
            fatal.append(f"第 {index - 1} 与 {index} 段之间缺失 {gap:.1f} 秒")
        text = segment.get("text", "").strip()
        if text and text == previous_text:
            repeat_run += 1
            if repeat_run >= 3:
                repeats.append(index)
        else:
            repeat_run = 0
        previous_text = text
        previous_end = max(previous_end, end)

    coverage = previous_end / expected if expected else None
    if coverage is not None:
        if coverage < 0.90:
            fatal.append(f"尾部覆盖只有 {coverage:.1%}")
        elif coverage < 0.97:
            warnings.append(f"尾部覆盖为 {coverage:.1%}，需要人工核对片尾")
    if long_gaps:
        warnings.append(f"发现 {len(long_gaps)} 个超过 30 秒的静音或缺口")
    if repeats:
        warnings.append("发现可能的连续重复转写")

    report = {
        "status": "fail" if fatal else "pass_with_warnings" if warnings else "pass",
        "expected_duration": expected, "last_segment_end": previous_end,
        "coverage": coverage, "segment_count": len(segments),
        "fatal": fatal, "warnings": warnings, "long_gaps": long_gaps, "repeat_segments": repeats,
        "manual_review_required": ["开头、中段、结尾", "人物与说话人归属", "专名、数字和直接引语"],
    }
    output = args.output or args.transcript.with_name("transcript-validation.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if fatal else 0)


if __name__ == "__main__":
    main()
