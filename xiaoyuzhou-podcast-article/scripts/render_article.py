#!/usr/bin/env python3
"""Render article.json with the fixed, readable HTML design."""

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def esc(value):
    return html.escape(str(value or ""), quote=True)


def render_block(block, article_dir: Path):
    kind = block.get("type")
    if kind == "paragraph":
        return f"<p>{esc(block.get('text'))}</p>"
    if kind == "quote":
        cite = f"<cite>— {esc(block.get('speaker'))}</cite>" if block.get("speaker") else ""
        return f"<blockquote>{esc(block.get('text'))}{cite}</blockquote>"
    if kind == "list":
        return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in block.get("items", [])) + "</ul>"
    if kind == "table":
        columns = block.get("columns") or []
        rows = block.get("rows") or []
        head = "".join(f"<th scope=\"col\">{esc(column)}</th>" for column in columns)
        body = "".join(
            "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in rows
        )
        caption = f"<caption>{esc(block.get('caption'))}</caption>" if block.get("caption") else ""
        note = f'<p class="table-note">{esc(block.get("note"))}</p>' if block.get("note") else ""
        return f'<div class="table-wrap"><table>{caption}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>{note}'
    if kind == "gallery":
        figures = []
        for item in block.get("items", []):
            src = item.get("src", "")
            if not src or not (article_dir / src).is_file():
                raise ValueError(f"图片不存在：{src}")
            caption = f"<figcaption>{esc(item.get('caption'))}</figcaption>" if item.get("caption") else ""
            figures.append(
                f'<figure><a class="figure-link" href="{esc(src)}" target="_blank" rel="noopener" '
                f'aria-label="查看原尺寸图片：{esc(item.get("alt"))}">'
                f'<img src="{esc(src)}" alt="{esc(item.get("alt"))}" loading="lazy"></a>{caption}</figure>'
            )
        return '<div class="figure-gallery">' + ''.join(figures) + '</div>'
    if kind == "figure":
        src = block.get("src", "")
        if not src or not (article_dir / src).is_file():
            raise ValueError(f"图片不存在：{src}")
        caption = f"<figcaption>{esc(block.get('caption'))}</figcaption>" if block.get("caption") else ""
        return (
            f'<figure><a class="figure-link" href="{esc(src)}" target="_blank" rel="noopener" '
            f'aria-label="查看原尺寸图片：{esc(block.get("alt"))}">'
            f'<img src="{esc(src)}" alt="{esc(block.get("alt"))}" loading="lazy"></a>{caption}</figure>'
        )
    raise ValueError(f"未知正文块类型：{kind}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("article", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.article.read_text(encoding="utf-8"))
    required = ["title", "podcast", "episode_url", "guide", "takeaways", "sections"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise SystemExit("article.json 缺少字段：" + ", ".join(missing))
    if len(data["takeaways"]) > 10:
        raise SystemExit("Key Takeaways 不得超过 10 条")

    css = (ROOT / "assets" / "article.css").read_text(encoding="utf-8")
    duration_min = round(float(data.get("duration_seconds", 0)) / 60)
    meta = f"{esc(data['podcast'])} · 原节目 {duration_min} 分钟"
    if data.get("reading_minutes"):
        meta += f" · 约 {esc(data['reading_minutes'])} 分钟读完"
    guide = "".join(f"<p>{esc(p)}</p>" for p in data["guide"])
    takeaway_parts = []
    for item in data["takeaways"]:
        insight = ""
        if item.get("insight"):
            insight = f'<p class="takeaway-insight">{esc(item.get("insight"))}</p>'
        takeaway_parts.append(
            f'<article class="takeaway"><h3>{esc(item.get("title"))}</h3>'
            f'<p>{esc(item.get("detail"))}</p>{insight}</article>'
        )
    takeaways = "".join(takeaway_parts)
    sections = []
    for index, section in enumerate(data["sections"], 1):
        blocks = "".join(render_block(block, args.article.parent) for block in section.get("blocks", []))
        number = section.get("number") or f"{index:02d}"
        sections.append(
            f'<section class="chapter"><div class="chapter-meta">{esc(number)}　{esc(section.get("time"))}</div>'
            f'<h2>{esc(section.get("title"))}</h2>{blocks}</section>'
        )
    model = data.get("transcription_source", "逐字稿")
    source_note = (
        "本文由 AI 根据节目音频、逐字稿和 Show Notes 整理，用于提高阅读效率；"
        f"转写来源：{esc(model)}。内容以原节目为准。"
    )
    document = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(data['title'])}</title><style>{css}</style></head><body><main>
<header class="masthead"><div class="eyebrow">播客阅读版</div><h1>{esc(data['title'])}</h1><p class="deck">{meta} · <a href="{esc(data['episode_url'])}">播客来源 ↗</a></p></header>
<section class="lead"><h2>导读</h2>{guide}</section>
<section class="takeaways"><h2>Key Takeaways</h2>{takeaways}</section>
{''.join(sections)}
<footer class="source-note">{source_note} <a href="{esc(data['episode_url'])}">查看原节目</a></footer>
</main>
<div class="image-viewer" role="dialog" aria-modal="true" aria-label="图片查看器" hidden>
  <button class="image-viewer-close" type="button" aria-label="关闭图片">×</button>
  <img src="" alt="">
</div>
<script>
(() => {{
  const viewer = document.querySelector('.image-viewer');
  const viewerImage = viewer.querySelector('img');
  const close = () => {{ viewer.hidden = true; viewerImage.src = ''; viewerImage.alt = ''; document.body.classList.remove('viewer-open'); }};
  document.querySelectorAll('.figure-link').forEach(link => link.addEventListener('click', event => {{
    event.preventDefault();
    const image = link.querySelector('img');
    viewerImage.src = link.getAttribute('href');
    viewerImage.alt = image ? image.alt : '';
    viewer.hidden = false;
    document.body.classList.add('viewer-open');
    viewer.querySelector('.image-viewer-close').focus();
  }}));
  viewer.addEventListener('click', close);
  document.addEventListener('keydown', event => {{ if (event.key === 'Escape' && !viewer.hidden) close(); }});
}})();
</script>
</body></html>'''
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
