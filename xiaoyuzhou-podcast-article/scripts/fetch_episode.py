#!/usr/bin/env python3
"""Fetch a public Xiaoyuzhou episode and inventory its first-party materials."""

import argparse
import html
import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


UA = "Mozilla/5.0 (compatible; XiaoyuzhouPodcastArticle/1.0)"


def request_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def safe_name(value: str, limit: int = 72) -> str:
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return (value[:limit].rstrip() or "episode")


def find_episode(node):
    if isinstance(node, dict):
        if node.get("type") == "EPISODE" and node.get("title") and node.get("duration"):
            return node
        for value in node.values():
            found = find_episode(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_episode(value)
            if found:
                return found
    return None


def extract_episode(page: str):
    match = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', page, re.S)
    if match:
        data = json.loads(html.unescape(match.group(1)))
        episode = find_episode(data)
        if episode:
            return episode
    for match in re.finditer(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', page, re.S):
        try:
            episode = find_episode(json.loads(html.unescape(match.group(1))))
        except json.JSONDecodeError:
            continue
        if episode:
            return episode
    raise RuntimeError("页面中没有找到公开的单集数据")


class ShowNotesParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.recent_text = []

    def handle_data(self, data):
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.recent_text.append(text)
            self.recent_text = self.recent_text[-5:]

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        attrs = dict(attrs)
        src = attrs.get("src") or attrs.get("data-src")
        if src:
            self.images.append({
                "source_index": len(self.images) + 1,
                "source_url": html.unescape(src),
                "alt": attrs.get("alt", ""),
                "nearby_text": " ".join(self.recent_text)[-300:],
            })


def caption_segments(node):
    """Accept only actual timestamped text, never a media ID alone."""
    candidates = []
    if isinstance(node, dict):
        keys = {k.lower(): k for k in node}
        text_key = next((keys[k] for k in ("text", "content", "sentence") if k in keys), None)
        start_key = next((keys[k] for k in ("start", "starttime", "start_time") if k in keys), None)
        end_key = next((keys[k] for k in ("end", "endtime", "end_time") if k in keys), None)
        if text_key and start_key and end_key and isinstance(node.get(text_key), str):
            candidates.append({"start": node[start_key], "end": node[end_key], "text": node[text_key]})
        for value in node.values():
            candidates.extend(caption_segments(value))
    elif isinstance(node, list):
        for value in node:
            candidates.extend(caption_segments(value))
    return candidates


def download(url: str, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".part")
    tmp.write_bytes(request_bytes(url))
    tmp.replace(destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--output-root", type=Path, default=Path.home() / "Desktop" / "xiaoyuzhou-podcast-article")
    parser.add_argument("--html-file", type=Path, help="Use a saved page instead of the network")
    args = parser.parse_args()

    parsed = urllib.parse.urlparse(args.url)
    if parsed.hostname not in {"www.xiaoyuzhoufm.com", "xiaoyuzhoufm.com"} or not re.fullmatch(r"/episode/[A-Za-z0-9]+/?", parsed.path):
        raise SystemExit("只接受 https://www.xiaoyuzhoufm.com/episode/<id> 单集链接")

    page = args.html_file.read_text(encoding="utf-8") if args.html_file else request_bytes(args.url).decode("utf-8", "replace")
    episode = extract_episode(page)
    episode_dir = args.output_root.expanduser().resolve() / safe_name(episode["title"])
    work = episode_dir / ".work"
    assets = episode_dir / "assets"
    work.mkdir(parents=True, exist_ok=True)
    assets.mkdir(parents=True, exist_ok=True)

    shownotes = episode.get("shownotes") or ""
    (work / "shownotes.html").write_text(shownotes, encoding="utf-8")
    episode_record = {
        "source_url": args.url,
        "eid": episode.get("eid"),
        "title": episode.get("title"),
        "description": episode.get("description"),
        "duration": episode.get("duration"),
        "pubDate": episode.get("pubDate"),
        "podcast": episode.get("podcast"),
        "enclosure": episode.get("enclosure"),
        "transcript": episode.get("transcript"),
        "transcriptMediaId": episode.get("transcriptMediaId"),
    }
    (work / "episode.json").write_text(json.dumps(episode_record, ensure_ascii=False, indent=2), encoding="utf-8")

    note_parser = ShowNotesParser()
    note_parser.feed(shownotes)
    for item in note_parser.images:
        suffix = Path(urllib.parse.urlparse(item["source_url"]).path).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            suffix = ".jpg"
        filename = f"show-notes-{item['source_index']:02d}{suffix}"
        try:
            download(item["source_url"], assets / filename)
            item["local_file"] = f"assets/{filename}"
            item["download_status"] = "ok"
        except Exception as exc:
            item["local_file"] = None
            item["download_status"] = f"error: {exc}"
    (work / "image-inventory.json").write_text(json.dumps(note_parser.images, ensure_ascii=False, indent=2), encoding="utf-8")
    failed_images = [item for item in note_parser.images if item["download_status"] != "ok"]
    if failed_images:
        print(f"警告：{len(failed_images)} 张 Show Notes 图片下载失败；正式成文前必须补齐", file=sys.stderr)

    captions = caption_segments(episode.get("transcript"))
    if captions:
        (work / "captions.json").write_text(json.dumps({"source": "xiaoyuzhou_page", "segments": captions}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(episode_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"获取失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
