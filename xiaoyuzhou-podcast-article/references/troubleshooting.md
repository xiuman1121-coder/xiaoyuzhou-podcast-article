# 故障处理

## 找不到 FFmpeg 或 ffprobe

先运行 `ffmpeg -version` 与 `ffprobe -version`。macOS 可用 Homebrew，Windows 可用 winget，Linux 使用发行版包管理器安装。两者负责媒体检查和必要时转码，不负责语音识别。

## 模型下载失败

`faster-whisper` 首次使用 `small` 或 `base` 时需要联网下载模型。保留错误信息，不要转用云端 API。网络恢复后重试同一模型；模型已手动下载时可把目录传给 `--model-path`。

## small 无法运行

确认磁盘空间和内存。若属于资源不足，改用 `base`，并在结果中记录实际模型。不要静默更换。

## 音频无法解码

先用 ffprobe 检查，再让 faster-whisper 直接读取。直接读取失败时，用 ffmpeg 生成 `.work/audio-16k.wav` 后重试一次。仍失败就输出失败报告并停止。

## 转写不完整

查看 `.work/transcript-validation.json` 中的尾部覆盖、长缺口和时间倒序。重新下载音频并比较 ffprobe 时长；必要时重新转写一次。缺失仍存在时不生成正式文章。

## 说话人或专名不确定

回到相邻时间段、节目自我介绍和 Show Notes 核对。官方图文版只能校正这些具体项目。无法唯一确认时使用保守描述；关键归属不确定时省略或标记待核对。
