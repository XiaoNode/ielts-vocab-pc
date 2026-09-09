#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅思/中考/高考 三档词库生成脚本
================================
从 ECDICT（MIT）筛选三档词库，关联 Tatoeba（CC BY 2.0 FR）双语例句，
输出单 bundle（每词带 libs 字段标记所属词库），供前端按库切换过滤。

词库档位（入门 → 进阶）：
  zk    中考：ECDICT tag 含 "zk"（约 1597 词）
  gk    高考：ECDICT tag 含 "gk"（约 3674 词，含大部分中考词）
  ielts 雅思：ECDICT tag 含 "ielts"（约 5013 词）+ Collins 星级词补齐到 target

进度互通：前端以 word 字符串为 key 存 localStorage，同一词在多库出现时进度天然共享。

用法：
  python scripts/generate-lexicon.py [ielts_target_count]
  默认 ielts_target_count = 8000
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

IELTS_TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

# 库定义顺序（入门 → 进阶）
LIBRARIES = [
    ("zk", "中考"),
    ("gk", "高考"),
    ("ielts", "雅思"),
]


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


def select_by_tags(words, tags):
    """按标签筛选（tags 任一命中）"""
    out = [w for w in words.values() if any(t in w["tags"] for t in tags)]
    out.sort(key=lambda x: (x["frq"], x["word"]))
    return out


def select_ielts(words, target):
    """雅思档：ielts 全量 + collins 星级词补齐到 target"""
    ielts = [w for w in words.values() if "ielts" in w["tags"]]
    ielts.sort(key=lambda x: x["frq"])

    non_ielts = [w for w in words.values() if "ielts" not in w["tags"]]
    collins_words = [w for w in non_ielts if w["collins"] >= 1]
    collins_words.sort(key=lambda x: x["frq"])

    selected = list(ielts)
    have = set(w["word"] for w in selected)

    need = target - len(selected)
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


def _read_bz2_tolerant(path):
    """容错读取 bz2：忽略截断（缺少 end-of-stream 标记），返回全部已解压文本"""
    import bz2
    dec = bz2.BZ2Decompressor()
    out = []
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            try:
                out.append(dec.decompress(chunk))
            except EOFError:
                # 文件截断：停止解压，已解压部分继续可用
                break
    return b"".join(out).decode("utf-8", errors="replace")


def _open_lines(path_tsv, path_bz2):
    """优先读解压后的 tsv，否则容错读 bz2（容忍截断）"""
    if os.path.exists(path_tsv):
        return open(path_tsv, "r", encoding="utf-8", errors="replace")
    return _read_bz2_tolerant(path_bz2).splitlines()


def load_tatoeba():
    """加载 Tatoeba 英中句对，返回 sentence 索引"""
    print("  loading Tatoeba sentences...")
    eng = {}   # id -> text
    cmn = {}   # id -> text
    links = []  # (eng_id, cmn_id)

    for line in _open_lines(ENG_SENT_TSV, ENG_SENT):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3:
            eng[parts[0]] = parts[2]
    for line in _open_lines(CMN_SENT_TSV, CMN_SENT):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3:
            cmn[parts[0]] = parts[2]
    for line in _open_lines(ENG_CMN_LINKS_TSV, ENG_CMN_LINKS):
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
        # 例句长度限制：6-18 词
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
    print("[1/5] Loading ECDICT ...")
    words = load_ecdict()
    print(f"  valid entries: {len(words)}")

    print("[2/5] Selecting libraries ...")
    zk_sel = select_by_tags(words, ["zk"])
    gk_sel = select_by_tags(words, ["gk"])
    ielts_sel = select_ielts(words, IELTS_TARGET)
    lib_sels = {"zk": zk_sel, "gk": gk_sel, "ielts": ielts_sel}
    for key, _name in LIBRARIES:
        print(f"  {key}({_name}): {len(lib_sels[key])} words")

    # 合并去重：word -> entry + libs 数组
    print("[3/5] Merging libraries ...")
    merged = {}  # word -> dict
    for key, _name in LIBRARIES:
        for w in lib_sels[key]:
            word = w["word"]
            if word not in merged:
                merged[word] = dict(w)
                merged[word]["libs"] = []
            if key not in merged[word]["libs"]:
                merged[word]["libs"].append(key)

    selected = list(merged.values())
    selected.sort(key=lambda x: (x["frq"], x["word"]))

    use_tatoeba = (
        (os.path.exists(ENG_SENT_TSV) or os.path.exists(ENG_SENT))
        and (os.path.exists(CMN_SENT_TSV) or os.path.exists(CMN_SENT))
        and (os.path.exists(ENG_CMN_LINKS_TSV) or os.path.exists(ENG_CMN_LINKS))
    )
    if use_tatoeba:
        print("[4/5] Loading Tatoeba ...")
        eng, cmn, links = load_tatoeba()
        idx = build_example_index(eng, cmn, links)
        selected = attach_examples(selected, idx)
    else:
        print("[4/5] Tatoeba not found, skipping examples (will use empty)")
        for w in selected:
            w["example"] = ""
            w["example_cn"] = ""

    print("[5/5] Writing lexicon.json + lexicon-data.js ...")
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
            libs=w["libs"],
            example=w["example"],
            example_cn=w["example_cn"],
        ))

    libraries = {}
    for key, name in LIBRARIES:
        libraries[key] = dict(key=key, name=name, count=len(lib_sels[key]))

    manifest = dict(
        name="ielts-vocab-multi",
        version="2.0.0",
        license="ECDICT: MIT; Tatoeba sentences: CC BY 2.0 FR",
        total=len(out),
        libraries=libraries,
        default_library="zk",
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
