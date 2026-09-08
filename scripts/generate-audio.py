#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频生成脚本（构建期）
=====================
为词库中的每个单词生成英式(GB)与美式(US)发音 WAV 文件，输出到 public/data/audio/。

方案优先级：
  1. espeak-ng（GPLv3）：离线 TTS，可本地生成标准音素音频 —— 首选
  2. 运行时兜底：前端用浏览器 SpeechSynthesis（无需本脚本）

用法（需已安装 espeak-ng 并加入 PATH）：
  python scripts/generate-audio.py
  python scripts/generate-audio.py --limit 100   # 只生成前 100 词（测试）

注意：
  - espeak-ng 为合成音，非真人发音，但完全离线、可商用分发（GPLv3 需开源衍生）。
  - 若追求真人发音，可后续替换为 CMUdict + 开源真人音频集。
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEXICON = os.path.join(BASE, "public", "data", "lexicon.json")
OUT_DIR = os.path.join(BASE, "public", "data", "audio")

VOICE_MAP = {
    "us": "en-us",  # espeak-ng 美音 voice
    "gb": "en-gb",  # espeak-ng 英音 voice
}

# espeak-ng 可执行文件路径（Windows 默认安装位置）
ESPEAK = None
for cand in [
    r"C:\Program Files\eSpeak NG\espeak-ng.exe",
    r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe",
    "espeak-ng",
]:
    if cand == "espeak-ng":
        # 检查是否在 PATH
        import shutil
        if shutil.which("espeak-ng"):
            ESPEAK = "espeak-ng"
            break
    elif os.path.exists(cand):
        ESPEAK = cand
        break


def load_words():
    with open(LEXICON, encoding="utf-8") as f:
        data = json.load(f)
    return data["words"]


def gen_one(word, accent, voice):
    out_path = os.path.join(OUT_DIR, f"{word}_{accent}.wav")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return True
    cmd = [ESPEAK, "-v", voice, "-s", "150", "-w", out_path, word]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=10)
        return True
    except Exception as e:
        return False


def main():
    if not ESPEAK:
        print("ERROR: espeak-ng 未找到，请先安装（winget install espeak-ng.espeak-ng）")
        sys.exit(1)

    limit = None
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        limit = int(sys.argv[i + 1])

    words = load_words()
    if limit:
        words = words[:limit]

    os.makedirs(OUT_DIR, exist_ok=True)

    # 构建所有 (word, accent, voice) 任务
    tasks = []
    for w in words:
        for accent, voice in VOICE_MAP.items():
            tasks.append((w["word"], accent, voice))

    ok = 0
    fail = 0
    done = 0
    total = len(tasks)

    # 并行生成（8 线程，espeak-ng 为轻量进程）
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(gen_one, t[0], t[1], t[2]): t for t in tasks}
        for fut in as_completed(futures):
            done += 1
            if fut.result():
                ok += 1
            else:
                fail += 1
            if done % 2000 == 0:
                print(f"  progress: {done}/{total} (ok={ok}, fail={fail})")

    print(f"DONE: ok={ok}, fail={fail}, total={total}")


if __name__ == "__main__":
    main()
