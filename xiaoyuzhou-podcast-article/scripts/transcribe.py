#!/usr/bin/env python3
"""Transcribe a Xiaoyuzhou CDN URL with Alibaba Model Studio paraformer-v2."""

import argparse
import json
import os
import shlex
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
MODEL = "paraformer-v2"
PRICE_PER_SECOND_CNY = 0.00008
TERMINAL = {"SUCCEEDED", "FAILED", "CANCELED", "UNKNOWN"}


class TranscriptionError(RuntimeError):
    pass


def setting(name):
    if os.environ.get(name):
        return os.environ[name]
    path = Path.home() / ".config" / "xiaoyuzhou-podcast-article" / "env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                values = shlex.split(line.split("=", 1)[1])
                return values[0] if values else ""
    return ""


def fail_message(status, payload):
    code = str(payload.get("code") or payload.get("Code") or "")
    message = str(payload.get("message") or payload.get("Message") or payload)
    joined = f"{code} {message}"
    if "AllocationQuota.FreeTierOnly" in joined:
        return "本月免费额度已经耗尽；任务已停止，未自动转为付费调用"
    if "Arrearage" in joined or "OUT_OF_SERVICE" in joined or "balance" in joined.lower():
        return "阿里云账户欠费或余额不足；任务已停止"
    if status in {401, 403}:
        detail = f"（{code}: {message}）" if code or message else ""
        return f"API Key 无效、地域不匹配或没有 paraformer-v2 权限{detail}"
    if "InvalidFile.DownloadFailed" in joined:
        return "阿里云无法读取小宇宙音频 CDN 地址"
    return f"阿里云请求失败（HTTP {status}）：{code or message}"


def request_json(method, url, api_key, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.update({"Authorization": f"Bearer {api_key}"})
    body = kwargs.pop("json", None)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"message": raw[:1000]}
        raise TranscriptionError(fail_message(exc.code, payload)) from exc


def episode_audio(episode_path):
    episode = json.loads(episode_path.read_text(encoding="utf-8"))
    enclosure = episode.get("enclosure") or {}
    url = enclosure.get("url") if isinstance(enclosure, dict) else None
    if not url:
        raise TranscriptionError("episode.json 中没有公开音频 CDN 地址")
    return episode, url


def submit(api_key, audio_url, diarization=False, speaker_count=None):
    parameters = {
        "channel_id": [0],
        "language_hints": ["zh", "en"],
        "disfluency_removal_enabled": False,
        "timestamp_alignment_enabled": True,
        "diarization_enabled": diarization,
    }
    if diarization and speaker_count:
        parameters["speaker_count"] = speaker_count
    payload = {"model": MODEL, "input": {"file_urls": [audio_url]}, "parameters": parameters}
    data = request_json(
        "POST", f"{setting('DASHSCOPE_BASE_URL') or DEFAULT_BASE_URL}/services/audio/asr/transcription", api_key,
        headers={"Content-Type": "application/json", "X-DashScope-Async": "enable"},
        json=payload,
    )
    return data["output"]["task_id"]


def wait(api_key, task_id, poll_seconds, timeout_seconds):
    started = time.monotonic()
    while True:
        base_url = setting("DASHSCOPE_BASE_URL") or DEFAULT_BASE_URL
        data = request_json("POST", f"{base_url}/tasks/{task_id}", api_key)
        output = data.get("output") or {}
        status = output.get("task_status")
        if status in TERMINAL:
            if status != "SUCCEEDED":
                raise TranscriptionError(f"云端转写任务未完成：{status}；{output.get('message', '')}")
            return output
        if time.monotonic() - started > timeout_seconds:
            raise TranscriptionError(f"等待云端任务超过 {timeout_seconds} 秒，已停止轮询；任务 ID：{task_id}")
        time.sleep(poll_seconds)


def find_sentences(result):
    candidates = []
    for transcript in result.get("transcripts") or []:
        candidates.extend(transcript.get("sentences") or [])
    if candidates:
        return candidates

    def walk(node):
        if isinstance(node, dict):
            if all(k in node for k in ("text", "begin_time", "end_time")) and "sentence_id" in node:
                candidates.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(result)
    return candidates


def normalize(result, elapsed, duration):
    rows = []
    for sentence in find_sentences(result):
        text = str(sentence.get("text") or "").strip()
        if not text:
            continue
        row = {
            "id": len(rows) + 1,
            "start": float(sentence["begin_time"]) / 1000,
            "end": float(sentence["end_time"]) / 1000,
            "text": text,
        }
        speaker = sentence.get("speaker_id", sentence.get("speaker"))
        if speaker is not None:
            row["speaker_id"] = speaker
        rows.append(row)
    if not rows:
        raise TranscriptionError("阿里云返回成功，但结果中没有可用的带时间戳句子")
    return {
        "text": "".join(row["text"] for row in rows),
        "segments": rows,
        "elapsed_seconds": elapsed,
        "model": MODEL,
        "language": "zh-en",
        "duration": duration or rows[-1]["end"],
        "source": "aliyun_model_studio",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", type=Path, help=".work/episode.json")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--allow-paid", action="store_true", help="仅在用户已明确同意本期付费后使用")
    parser.add_argument("--diarization", action="store_true")
    parser.add_argument("--speaker-count", type=int)
    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    args = parser.parse_args()

    api_key = setting("DASHSCOPE_API_KEY").strip()
    if not api_key:
        raise TranscriptionError("未配置 DASHSCOPE_API_KEY；请先完成阿里云百炼设置")
    if not args.allow_paid and setting("DASHSCOPE_FREE_TIER_STOP_CONFIRMED") != "1":
        raise TranscriptionError(
            "尚未确认已为 paraformer-v2 开启“免费额度用完即停”；请完成设置后将 "
            "DASHSCOPE_FREE_TIER_STOP_CONFIRMED=1"
        )

    episode, audio_url = episode_audio(args.episode)
    duration = float(episode.get("duration") or 0)
    estimate = duration * PRICE_PER_SECOND_CNY
    if args.allow_paid:
        print(f"本次已获明确付费许可；按当前公开单价估算最多约 ¥{estimate:.2f}", file=sys.stderr)
    started = time.monotonic()
    task_id = submit(api_key, audio_url, args.diarization, args.speaker_count)
    output = wait(api_key, task_id, args.poll_seconds, args.timeout_seconds)
    results = output.get("results") or []
    success = next((item for item in results if item.get("subtask_status") == "SUCCEEDED"), None)
    if not success or not success.get("transcription_url"):
        raise TranscriptionError(f"任务成功但没有可下载的逐字稿结果：{output}")
    with urllib.request.urlopen(success["transcription_url"], timeout=60) as result_response:
        result_data = json.loads(result_response.read().decode("utf-8"))
    transcript = normalize(result_data, time.monotonic() - started, duration)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "transcript.json").write_text(
        json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [f"[{row['start']:.2f}–{row['end']:.2f}] {row['text']}" for row in transcript["segments"]]
    (args.output_dir / "transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"完成：{len(lines)} 段，耗时 {transcript['elapsed_seconds']:.1f} 秒，模型 {MODEL}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
