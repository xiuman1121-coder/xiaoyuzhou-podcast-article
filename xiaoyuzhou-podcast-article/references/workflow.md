# 运行流程

## 环境与目录

支持 macOS、Windows 和 Linux 桌面系统，要求 Python 3.9+ 和 `faster-whisper`。建议安装 FFmpeg/ffprobe，用于媒体时长检查、损坏排查和必要时转码；正常情况下 `faster-whisper` 可以直接解码，流程不会为了形式而额外转码。手机端不在首版支持范围内。

默认根目录是 `~/Desktop/xiaoyuzhou-podcast-article`。所有脚本都接受显式路径，因此桌面不存在或不可写时，先让用户选择一个可写目录。

每期单独建立目录，最终结构为：

```text
单集名称/
├── index.html
├── transcript.txt
├── transcript.json
├── source-map.json
├── image-decisions.json
├── data-points.json
├── content-profile.json
├── argument-map.json
├── assets/
└── .work/
    ├── episode.json
    ├── shownotes.html
    ├── image-inventory.json
    ├── transcript-validation.json
    └── audio.<扩展名>   # 完成或终止后删除
```

## 1. 获取节目

```bash
python scripts/fetch_episode.py "<小宇宙链接>" --output-root "<根目录>" --download-audio
```

脚本输出单集目录路径。它只接受公开的 `xiaoyuzhoufm.com/episode/<id>`，保存页面原始节目数据、Show Notes 和全部 Show Notes 图片。

## 2. 字幕优先判断

若 `.work/captions.json` 存在，先运行逐字稿检查。字幕必须有连续时间戳、覆盖节目主体且抽查无系统性错乱。页面只有 transcript/media ID 而没有字幕正文，不算可用字幕；继续本地转写。

## 3. 本地转写

```bash
python scripts/transcribe.py "<单集目录>/.work/audio.mp3" "<单集目录>" --model small --prompt "节目名、嘉宾名、产品名及已确认术语"
```

默认 `small`，CPU int8，本地运行，不需要 API Key。若模型因内存或设备能力无法启动，改用 `--model base`。不要同时安装或尝试多个其他 Whisper 实现。

`ffprobe` 用于读取媒体时长并发现明显损坏；`ffmpeg` 用于无法直接解码时转换为临时 16 kHz 单声道 WAV。`faster-whisper` 能直接读取时不必转换。

## 4. 检查逐字稿

```bash
python scripts/validate_transcript.py "<单集目录>/transcript.json" --episode "<单集目录>/.work/episode.json" --output "<单集目录>/.work/transcript-validation.json"
```

脚本检查空稿、时间倒序、节目尾部缺失、异常长缺口和重复。通过后仍需抽查开头、中段、结尾及包含专名/数字的片段。

如果失败：可以重新下载一次、重新解码一次、换 `base` 一次。仍失败就停止，运行 `scripts/write_failure_report.py`，记录已完成阶段、失败证据、缺失范围和已尝试动作。不得继续生成看似完整的文章。

## 5. 分段整理

读取 `references/editorial-rules.md`。先建立 `content-profile.json` 判断内容形态和压缩风险，再依据时间戳与 Show Notes 建章节。为核心观点建立 `argument-map.json`，然后一次处理一个时间段。每完成一段，同时更新 `article.json` 与 `source-map.json`。图片和明确数据都需先完成全量清单，再作取舍；支撑核心判断的数据不得被概括成没有数值的泛称。阅读时间在内容完成后估算，不预先设定硬上限。

官方图文版只用于逐项校正，不作为文章底稿。其他外链默认不打开。

## 6. 渲染、审计与清理

```bash
python scripts/render_article.py "<单集目录>/article.json" "<单集目录>/index.html"
python scripts/audit_package.py "<单集目录>"
python scripts/cleanup_audio.py "<单集目录>"
```

审计失败时先修正文章或来源记录。只有审计通过的 `index.html` 才作为正式成品。音频删除后保留逐字稿、来源表、图片和 HTML。
