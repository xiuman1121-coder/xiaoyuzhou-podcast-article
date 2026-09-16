#!/usr/bin/env python3
"""Audit required files, title fidelity, source coverage, and image decisions."""

import argparse
import json
import re
from pathlib import Path


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_dir", type=Path)
    args = parser.parse_args()
    root = args.episode_dir
    errors, warnings = [], []
    required = ["index.html", "article.json", "transcript.txt", "transcript.json", "source-map.json", "image-decisions.json", "data-points.json", "content-profile.json", "argument-map.json"]
    for name in required:
        if not (root / name).is_file():
            errors.append(f"缺少 {name}")
    if errors:
        print("FAIL\n" + "\n".join(f"- {e}" for e in errors))
        raise SystemExit(1)

    article, episode = load(root / "article.json"), load(root / ".work" / "episode.json")
    if article.get("title") != episode.get("title"):
        errors.append("article.json 标题与小宇宙原始标题不一致")
    count = len(article.get("takeaways", []))
    if not 3 <= count <= 7:
        warnings.append(f"Key Takeaways 为 {count} 条；通常应为 3–7 条")
    normalized = [re.sub(r"\s+", "", (x.get("title", "") + x.get("detail", ""))) for x in article.get("takeaways", [])]
    if len(normalized) != len(set(normalized)):
        errors.append("存在完全重复的 Key Takeaway")

    source_map = load(root / "source-map.json")
    if not source_map.get("items"):
        errors.append("source-map.json 没有来源记录")
    inventory = load(root / ".work" / "image-inventory.json")
    decisions = load(root / "image-decisions.json")
    failed_images = [item for item in inventory if item.get("download_status") != "ok"]
    if failed_images:
        errors.append(f"有 {len(failed_images)} 张 Show Notes 图片未成功下载，无法完成全量判断")
    if len(inventory) != len(decisions):
        errors.append(f"图片取舍记录不完整：原图 {len(inventory)} 张，记录 {len(decisions)} 张")
    for item in decisions:
        if item.get("decision") not in {"include", "exclude"} or not item.get("reason"):
            errors.append(f"第 {item.get('source_index')} 张图片缺少明确取舍或理由")
    data_points = load(root / "data-points.json")
    for index, item in enumerate(data_points, 1):
        if item.get("decision") not in {"include", "exclude"} or not item.get("reason"):
            errors.append(f"第 {index} 条数据缺少明确取舍或理由")
        if item.get("decision") == "include" and not item.get("article_location"):
            errors.append(f"第 {index} 条采用数据没有文章位置")
    profile = load(root / "content-profile.json")
    if not profile.get("content_type") or not profile.get("compression_risk"):
        errors.append("content-profile.json 缺少内容类型或压缩风险判断")
    argument_map = load(root / "argument-map.json")
    if not argument_map.get("arguments"):
        errors.append("argument-map.json 没有核心观点覆盖记录")
    for index, item in enumerate(argument_map.get("arguments", []), 1):
        if item.get("coverage_status") not in {"covered", "source_gap"}:
            errors.append(f"第 {index} 条核心观点没有完成覆盖或标明节目自身的证据缺口")

    status = "FAIL" if errors else "PASS WITH WARNINGS" if warnings else "PASS"
    print(status)
    for issue in errors:
        print(f"ERROR: {issue}")
    for issue in warnings:
        print(f"WARNING: {issue}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
