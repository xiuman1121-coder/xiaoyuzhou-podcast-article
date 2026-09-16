# 小宇宙播客阅读版

一个 Codex Skill：把公开的小宇宙单集整理成忠实、可追溯、适合中文阅读的 HTML 文章，并允许用户继续基于完整逐字稿提问。

当前版本：`v1.0.0`。

它会保存带时间戳的逐字稿和来源表，先逐段整理，再用固定模板生成 `index.html`。阅读时间由最终信息量决定，不作为删减目标。Show Notes 图片会全部盘点；PPT 驱动节目默认保留所有承载独立信息的页面，并检查核心观点的推理链与证据链。遇到音频或逐字稿缺失时会停止并写失败报告，不会自行补齐内容。

## 支持范围

- 输入：公开的 `xiaoyuzhoufm.com/episode/...` 单集链接
- 语言：中文及中英混合音频，中文文章
- 系统：目前主要在 macOS 上验证；脚本按 Python 跨平台方式编写，但 Windows 和 Linux 尚未完成实机验证
- 语音识别：本地 `faster-whisper-small`，低资源设备可用 `faster-whisper-base`
- 输出：静态 HTML、逐字稿、来源表、图片取舍记录

暂不支持其他播客平台、手机端本地运行、云端转写 API 或 MLX Whisper。

## 安装

1. 安装 Python 3.9+。建议同时安装 FFmpeg 和 ffprobe，用于异常音频排查与转码。
2. 创建虚拟环境并安装依赖：

   ```bash
   python -m venv .venv
   .venv/bin/pip install -r xiaoyuzhou-podcast-article/requirements.txt
   ```

   Windows PowerShell 使用 `.venv\Scripts\pip.exe install -r xiaoyuzhou-podcast-article\requirements.txt`。

3. 将仓库中的 `xiaoyuzhou-podcast-article/` 子文件夹安装到 Codex 的 Skills 目录。不要把仓库根目录整体当作 Skill 安装；根目录的 README 和 LICENSE 面向 GitHub 访问者。

模型不随仓库发布。首次转写时，`faster-whisper` 会下载选择的 `small` 或 `base` 模型。

## 使用

可以显式调用：

```text
使用 $xiaoyuzhou-podcast-article 把这个链接转成文章：<小宇宙单集链接>
```

也可以直接说：

```text
帮我把这个小宇宙播客链接转成文章：<链接>
```

“转成文章”默认表示生成最终 HTML，不需要额外说明 HTML。输出默认保存在桌面的 `xiaoyuzhou-podcast-article` 文件夹，每期节目有独立子目录。

文章完成后可以直接继续提问，例如“Loop 是什么意思？”或“这个数据是主播的判断还是引用资料？”。回答会区分播客原意、Agent 的通俗转述和播客之外的补充，并尽量给出对应时间范围。

完整流程、失败处理与内容规则位于 Skill 子文件夹的 `references/`。脚本可单独运行，但通常由加载本 Skill 的 Agent 按 `SKILL.md` 编排。

只有逐字稿检查和内容审计通过后才交付正式 HTML。无法确认关键内容时，流程会停止并生成失败报告，不会用推测补齐。

## 隐私与网络

语音识别在本机完成，不需要 API Key。网络只用于读取公开的小宇宙页面、下载节目音频与 Show Notes 图片，以及首次下载 Whisper 模型。临时音频在成功完成或最终停止后删除。

## 许可

MIT License，见 [LICENSE](LICENSE)。
