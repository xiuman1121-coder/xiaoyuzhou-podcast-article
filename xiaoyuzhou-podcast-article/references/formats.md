# 数据格式

## article.json

```json
{
  "title": "原始节目标题",
  "podcast": "播客名",
  "author": "主播或出品方",
  "episode_url": "https://www.xiaoyuzhoufm.com/episode/...",
  "duration_seconds": 3600,
  "reading_minutes": 15,
  "transcription_source": "local_whisper_small",
  "guide": ["导读第一段", "导读第二段"],
  "takeaways": [{"title": "核心判断", "detail": "关键数据、案例或推理", "insight": "这项判断意味着什么或适用边界"}],
  "sections": [{
    "number": "01", "time": "00:00–08:20", "title": "章节标题",
    "blocks": [
      {"type": "paragraph", "text": "正文"},
      {"type": "quote", "text": "已核对原话", "speaker": "嘉宾"},
      {"type": "list", "items": ["一", "二"]},
      {"type": "table", "caption": "数据名称", "columns": ["对象", "数值"], "rows": [["A", "100 万"]], "note": "统计时间、单位与节目引用来源"},
      {"type": "gallery", "items": [{"src": "assets/02-slide.png", "alt": "准确替代文本", "caption": "图注"}]},
      {"type": "figure", "src": "assets/01-example.png", "alt": "准确替代文本", "caption": "图注"}
    ]
  }]
}
```

渲染器只接受 `paragraph`、`quote`、`list`、`table`、`figure` 和 `gallery`。文字会被 HTML 转义，不在 JSON 中写 HTML。

## transcript.json

包含 `text`、`segments`、`model`、`language`、`duration`、`elapsed_seconds` 与 `source`。每个 segment 包含递增的 `id`、`start`、`end` 和 `text`。

## source-map.json

`items` 数组中的每项包含 `article_path`、`start`、`end`、`segment_ids`、`speaker`、`speaker_confidence` 和 `notes`。至少覆盖导读、Takeaways、正文段落和直接引语。

## image-decisions.json

数组中必须包含 Show Notes 的全部图片。每项包含 `source_index`、`source_url`、`local_file`、`nearby_text`、`time_hint`、`information`、`related_claim`、`decision`、`reason` 和 `article_location`。

## data-points.json

数组中包含节目与 Show Notes 的明确数字。每项包含 `value`、`unit`、`subject`、`period`、`attribution`、`start`、`end`、`source_kind`（`spoken`、`slide` 或 `both`）、`decision`、`reason` 和 `article_location`。同组数字可以共享一个 `group` 字段。

## content-profile.json

记录 `content_type`、`density`、`primary_evidence`、`compression_risk` 和 `notes`。PPT 驱动型节目应把 `slides` 列为主要证据载体。

## argument-map.json

`arguments` 数组中的每项包含 `claim`、`source_range`、`premises`、`evidence`、`examples`、`counterpoints`、`caveats`、`article_locations` 和 `coverage_status`。节目没有提供某一层时保留空数组并写明缺口，不允许补造。
