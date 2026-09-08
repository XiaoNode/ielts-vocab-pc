#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅思词库生成脚本
================
从 ECDICT（MIT）筛选约 8000 个雅思相关单词，关联 Tatoeba（CC BY 2.0 FR）双语例句，
输出 public/data/lexicon.json 供前端加载。

筛选策略：
  L1 核心层：ECDICT tag 含 "ielts" 的词（约 5000 词）
  L2 补充层：非 ielts 但 Collins 有星级(1-5)的词，按词频(frq)升序取前 N 补齐到目标词量

用法：
  python scripts/generate-lexicon.py [target_count]
  默认 target_count = 8000
"""
import csv
import json
import os
import sys
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD = os.path.join(BASE, "scripts", "download")
SRC_DIR = os.path.join(BASE, "src")
OUT_DIR = os.path.join(BASE, "public", "data")
OUT_FILE = os.path.join(OUT_DIR, "lexicon.json")
OUT_ESM = os.path.join(SRC_DIR, "lexicon-data.js")  # 内联到 JS，供 file:// 双击直开

ECDICT = os.path.join(DOWNLOAD, "ecdict_full.csv")
# 优先读已解压的 .tsv（避免 bz2 截断问题）；若不存在则回退 .bz2
ENG_SENT_TSV = os.path.join(DOWNLOAD, "eng_sentences.tsv")
CMN_SENT_TSV = os.path.join(DOWNLOAD, "cmn_sentences.tsv")
ENG_CMN_LINKS_TSV = os.path.join(DOWNLOAD, "eng-cmn_links.tsv")
ENG_SENT = os.path.join(DOWNLOAD, "eng_sentences.tsv.bz2")
CMN_SENT = os.path.join(DOWNLOAD, "cmn_sentences.tsv.bz2")
ENG_CMN_LINKS = os.path.join(DOWNLOAD, "eng-cmn_links.tsv.bz2")

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
L2_TARGET = TARGET - 5013  # ielts 层固定约 5013 词


def is_pure_word(w: str) -> bool:
    """保留纯单词（允许撇号），排除短语/带空格/连字符的条目"""
    return bool(w) and w.replace("'", "").isalpha()


def load_ecdict():
    """读取 ECDICT，返回 {word: dict}"""
    words = {}
    with open(ECDICT, encoding="utf-8", errors="replace") as f:
        r = csv.reader(f)
        next(r)  # header
        for row in r:
            if len(row) < 13:
                continue
            word, phonetic, definition, translation, pos, collins, oxford, tag, bnc, frq, exchange, detail, audio = row[:13]
            w = word.strip()
            if not is_pure_word(w):
                continue
            if not translation.strip():
                continue
            tags = set(tag.split()) if tag else set()
            try:
                frq_i = int(frq) if frq else 999999
            except ValueError:
                frq_i = 999999
            try:
                coll_i = int(collins) if collins else 0
            except ValueError:
                coll_i = 0
            # 取第一个词性缩写
            pos_short = ""
            if pos:
                # 格式形如 "n:1" 或 "n"
                pos_short = pos.split(":")[0].strip()
            words[w] = dict(
                word=w, phonetic=phonetic, translation=translation.strip(),
                pos=pos_short, collins=coll_i, oxford=(oxford or "").strip(),
                tags=sorted(tags), frq=frq_i, audio=audio,
            )
    return words


def select_words(words, target):
    """分层筛选"""
    ielts = [w for w in words.values() if "ielts" in w["tags"]]
    ielts.sort(key=lambda x: x["frq"])

    non_ielts = [w for w in words.values() if "ielts" not in w["tags"]]
    collins_words = [w for w in non_ielts if w["collins"] >= 1]
    collins_words.sort(key=lambda x: x["frq"])

    selected = list(ielts)
    have = set(w["word"] for w in selected)

    need = target - len(selected)
    # 先取 collins 星级词，不够再按词频补
    fill = []
    for w in collins_words:
        if w["word"] not in have:
            fill.append(w)
            have.add(w["word"])
            if len(fill) >= need:
                break
    selected += fill

    if len(selected) < target:
        rest = [w for w in non_ielts if w["word"] not in have]
        rest.sort(key=lambda x: x["frq"])
        need2 = target - len(selected)
        selected += rest[:need2]

    selected.sort(key=lambda x: x["frq"])
    return selected


def _open_lines(path_tsv, path_bz2):
    """优先读解压后的 tsv，否则读 bz2"""
    if os.path.exists(path_tsv):
        return open(path_tsv, "r", encoding="utf-8", errors="replace")
    import bz2
    return bz2.open(path_bz2, "rt", encoding="utf-8", errors="replace")


def load_tatoeba():
    """加载 Tatoeba 英中句对，返回 {word: [{en, cn}]} 及 sentence 索引"""
    print("  loading Tatoeba sentences...")
    eng = {}   # id -> text
    cmn = {}   # id -> text
    links = []  # (eng_id, cmn_id)

    with _open_lines(ENG_SENT_TSV, ENG_SENT) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                eng[parts[0]] = parts[2]
    with _open_lines(CMN_SENT_TSV, CMN_SENT) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                cmn[parts[0]] = parts[2]
    with _open_lines(ENG_CMN_LINKS_TSV, ENG_CMN_LINKS) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                links.append((parts[0], parts[1]))

    print(f"  eng sentences: {len(eng)}, cmn sentences: {len(cmn)}, links: {len(links)}")
    return eng, cmn, links


def build_example_index(eng, cmn, links):
    """构建 单词 -> 例句列表 的索引（只保留有中文翻译的短句）"""
    print("  building example index...")
    idx = {}
    link_map = {}  # eng_id -> cmn_id
    for eid, cid in links:
        link_map[eid] = cid

    pat = re.compile(r"\b([A-Za-z']+)\b")
    for eid, text in eng.items():
        cid = link_map.get(eid)
        if not cid or cid not in cmn:
            continue
        cn = cmn[cid]
        # 例句长度限制：8-15 词最佳，最多 18
        tokens = text.split()
        if len(tokens) < 6 or len(tokens) > 18:
            continue
        for m in pat.finditer(text):
            w = m.group(1).lower()
            if w not in idx:
                idx[w] = []
            idx[w].append((text, cn))

    # 每词按例句长度排序（越短越简单优先）
    for w in idx:
        idx[w].sort(key=lambda x: len(x[0].split()))
    return idx


def attach_examples(selected, idx):
    """为每个词附加 1 条最佳例句"""
    print("  attaching examples...")
    matched = 0
    for w in selected:
        w["example"] = ""
        w["example_cn"] = ""
        cands = idx.get(w["word"].lower())
        if cands:
            w["example"] = cands[0][0]
            w["example_cn"] = cands[0][1]
            matched += 1
    print(f"  example matched: {matched}/{len(selected)}")
    return selected


def main():
    target = TARGET
    print(f"[1/4] Loading ECDICT ...")
    words = load_ecdict()
    print(f"  valid entries: {len(words)}")

    print(f"[2/4] Selecting {target} words ...")
    selected = select_words(words, target)
    ielts_n = sum(1 for w in selected if "ielts" in w["tags"])
    print(f"  selected: {len(selected)} (ielts: {ielts_n}, others: {len(selected)-ielts_n})")

    use_tatoeba = (
        (os.path.exists(ENG_SENT_TSV) or os.path.exists(ENG_SENT))
        and (os.path.exists(CMN_SENT_TSV) or os.path.exists(CMN_SENT))
        and (os.path.exists(ENG_CMN_LINKS_TSV) or os.path.exists(ENG_CMN_LINKS))
    )
    if use_tatoeba:
        print("[3/4] Loading Tatoeba ...")
        eng, cmn, links = load_tatoeba()
        idx = build_example_index(eng, cmn, links)
        selected = attach_examples(selected, idx)
    else:
        print("[3/4] Tatoeba not found, skipping examples (will use empty)")
        for w in selected:
            w["example"] = ""
            w["example_cn"] = ""

    print("[4/4] Writing lexicon.json ...")
    os.makedirs(OUT_DIR, exist_ok=True)

    # 精简输出字段
    out = []
    for w in selected:
        out.append(dict(
            word=w["word"],
            phonetic=w["phonetic"],
            translation=w["translation"],
            pos=w["pos"],
            collins=w["collins"],
            oxford=w["oxford"],
            frq=w["frq"],
            example=w["example"],
            example_cn=w["example_cn"],
        ))

    manifest = dict(
        name="ielts-vocab-core",
        version="1.0.0",
        license="ECDICT: MIT; Tatoeba sentences: CC BY 2.0 FR",
        total=len(out),
        ielts_count=ielts_n,
        generated_at="",
    )

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dict(manifest=manifest, words=out), f, ensure_ascii=False, separators=(",", ":"))

    # 同步生成 ES module 数据文件（供前端 import，绕过 file:// 下 fetch 的 CORS 限制）
    with open(OUT_ESM, "w", encoding="utf-8") as f:
        f.write("// 由 scripts/generate-lexicon.py 自动生成，请勿手改\n")
        f.write("export default ")
        json.dump(dict(manifest=manifest, words=out), f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    size = os.path.getsize(OUT_FILE)
    print(f"  written {OUT_FILE} ({size/1024/1024:.1f} MB, {len(out)} words)")
    print(f"  written {OUT_ESM}")
    print("DONE")


if __name__ == "__main__":
    main()
