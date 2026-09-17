# 运行流程

## 环境与目录

支持 Python 3.9+。没有本地语音模型，也不要求 FFmpeg。没有可用字幕时，使用用户自己的阿里云百炼华北 2（北京）API Key 调用 `paraformer-v2`。

默认根目录是 `~/Desktop/xiaoyuzhou-podcast-article`。每期单独建立目录，保留 HTML、逐字稿、来源表和图片；不保存原始音频。

## 1. 首次配置

用户必须在阿里云百炼华北 2（北京）创建 API Key，并为 `paraformer-v2` 开启“免费额度用完即停”。先在普通终端运行配置程序，绝不能直接把 Key 粘贴到 `%` 或 `$` 命令提示符：

```bash
python scripts/configure_api_key.py
```

必须等程序明确显示“API Key（隐藏输入）”后，才粘贴 Key 并按回车。输入过程不显示字符。程序随后要求粘贴同一页面显示的 OpenAI Compatible URL，并自动转换为语音识别 API 地址。然后运行：

```bash
python scripts/check_environment.py
```

配置保存在用户个人目录，不写入 Skill、输出目录或 Git 仓库。本地确认记录不能代替阿里云的服务端开关。若用户日后关闭开关，仍须在每次可能产生费用前取得明确许可。

## 2. 获取节目

```bash
python scripts/fetch_episode.py "<小宇宙链接>" --output-root "<根目录>"
```

脚本保存节目资料、公开音频 CDN URL、Show Notes 和全部图片，不下载原始音频。

## 3. 字幕优先判断

若 `.work/captions.json` 存在，先运行逐字稿检查。字幕必须有连续时间戳、覆盖节目主体且抽查无系统性错乱。只有 transcript/media ID 而没有字幕正文，不算可用字幕。

## 4. 云端转写

默认免费额度模式：

```bash
python scripts/transcribe.py "<单集目录>/.work/episode.json" "<单集目录>" --diarization
```

脚本把小宇宙 CDN URL 直接交给 `paraformer-v2`，轮询任务并将结果标准化为 `transcript.json` 和 `transcript.txt`。不使用 OSS 或本地转录 fallback。

免费额度耗尽时立即停止。只有用户看到本期费用估算、自行充值并关闭“免费额度用完即停”、明确同意本期付费后，才允许传入 `--allow-paid`。

## 5. 检查逐字稿

```bash
python scripts/validate_transcript.py "<单集目录>/transcript.json" --episode "<单集目录>/.work/episode.json" --output "<单集目录>/.work/transcript-validation.json"
```

检查空稿、时间倒序、尾部缺失、异常长缺口和重复。通过后仍需抽查开头、中段、结尾、专名和数字。失败时重新解析一次 CDN URL 并重试一次；仍失败则写失败报告并停止。

## 6. 分段整理与交付

读取 `references/editorial-rules.md`，按时间戳逐段整理并维护来源表、数据表、论证图和图片取舍记录。完成后运行渲染与审计。只有审计通过的 `index.html` 才作为正式成品。
