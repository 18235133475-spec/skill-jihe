#!/usr/bin/env python3
"""
横纵分析报告质检脚本（脚本化质检）
用法: python verify_report.py report.md [--research 研究底稿.json] [--min-words 10000] [--max-words 30000]

检查项：
  1. 必备章节完整性（一句话定义/纵向分析/横向分析/横纵交汇/信息来源）
  2. 引证闭环：正文 [S编号] 与「信息来源」清单一一对应；不允许占位符/假URL
  3. 字数区间（默认 10000-30000）
  4. 绝对禁区词扫描（AI味套话）
  5. 可选：与 schema 研究底稿的来源注册表交叉核对

退出码：有 ERROR 为 1，仅 WARN 或全部通过为 0。
"""

import argparse
import json
import re
import sys

REQUIRED_SECTIONS = ["一句话定义", "纵向分析", "横向分析", "横纵交汇", "信息来源"]

# 与 SKILL.md「绝对禁区」一致的禁词表
BANNED_PHRASES = [
    "综上所述", "值得注意的是", "不难发现", "说白了", "本质上", "换句话说",
    "不可否认", "赋能", "抓手", "打造闭环", "在当今", "随着技术的不断进步",
    "这意味着", "意味着什么",
]

PLACEHOLDER_PATTERNS = [
    r"example\.com", r"xxx", r"TODO", r"待补充", r"占位",
    r"https?://\s*$", r"链接暂缺(?!）)",  # 「暂缺」需带括号说明才合法
]

SID_PATTERN = re.compile(r"\[S(\d+)\]")
URL_PATTERN = re.compile(r"https?://[^\s）)\]】]+")


def count_words(text: str) -> int:
    """字数 = CJK 字符数 + 西文单词数"""
    cjk = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", text))
    latin = len(re.findall(r"[A-Za-z0-9]+", text))
    return cjk + latin


def split_sources_section(text: str) -> tuple[str, str]:
    """以「信息来源」标题为界，返回 (正文, 来源节)。找不到则来源节为空。"""
    m = re.search(r"^#{1,4}\s*.*信息来源.*$", text, re.M)
    if not m:
        return text, ""
    return text[: m.start()], text[m.start():]


def main() -> int:
    ap = argparse.ArgumentParser(description="横纵分析报告质检")
    ap.add_argument("report", help="报告 Markdown 文件")
    ap.add_argument("--research", help="研究底稿 JSON（按 references/schema.json）")
    ap.add_argument("--min-words", type=int, default=10000)
    ap.add_argument("--max-words", type=int, default=30000)
    args = ap.parse_args()

    text = open(args.report, encoding="utf-8").read()
    errors, warnings = [], []

    # ── 1. 必备章节 ──
    for sec in REQUIRED_SECTIONS:
        if not re.search(r"^#{1,4}\s*.*" + re.escape(sec), text, re.M):
            errors.append(f"缺少必备章节：{sec}")

    # ── 2. 引证闭环 ──
    body, src_section = split_sources_section(text)
    cited_ids = {int(n) for n in SID_PATTERN.findall(body)}
    defined_ids = {int(n) for n in SID_PATTERN.findall(src_section)}

    if not src_section:
        errors.append("缺少「信息来源」一节，引证无法闭环")
    else:
        for sid in sorted(cited_ids - defined_ids):
            errors.append(f"正文引用了 [S{sid}]，但信息来源清单中没有该编号")
        for sid in sorted(defined_ids - cited_ids):
            warnings.append(f"[S{sid}] 已在来源清单登记，但正文从未引用")
        # 每条来源必须带 URL 或明确的「暂缺」标注
        for sid in sorted(defined_ids):
            entry = re.search(r"\[S%d\](.*?)(?=\[S\d+\]|\Z)" % sid, src_section, re.S)
            entry_text = entry.group(1) if entry else ""
            if not URL_PATTERN.search(entry_text) and "暂缺" not in entry_text:
                errors.append(f"[S{sid}] 来源条目没有 URL，也没有「暂缺」标注")

    if body and not cited_ids:
        errors.append("正文中没有任何 [S编号] 引证——深度研究报告必须句句有出处")

    for pat in PLACEHOLDER_PATTERNS:
        m = re.search(pat, text)
        if m:
            line_no = text[: m.start()].count("\n") + 1
            errors.append(f"疑似占位符/假链接（第 {line_no} 行附近）：匹配 {pat}")

    # ── 3. 字数 ──
    wc = count_words(text)
    if wc < args.min_words:
        errors.append(f"字数 {wc} 低于下限 {args.min_words}")
    elif wc > args.max_words:
        warnings.append(f"字数 {wc} 超出上限 {args.max_words}")

    # ── 4. 绝对禁区词 ──
    for phrase in BANNED_PHRASES:
        for m in re.finditer(re.escape(phrase), text):
            line_no = text[: m.start()].count("\n") + 1
            errors.append(f"触犯绝对禁区词「{phrase}」（第 {line_no} 行）")

    # ── 5. 与研究底稿交叉核对（可选）──
    if args.research:
        try:
            research = json.load(open(args.research, encoding="utf-8"))
            registry = research.get("信息来源注册表", {}).get("来源条目", [])
            reg_ids = set()
            for item in registry:
                m = re.match(r"S(\d+)", str(item.get("编号", "")))
                if m:
                    reg_ids.add(int(m.group(1)))
            for sid in sorted(reg_ids - defined_ids):
                warnings.append(f"底稿注册表中的 [S{sid}] 未出现在报告来源清单")
            for sid in sorted(defined_ids - reg_ids):
                warnings.append(f"报告来源 [S{sid}] 不在底稿注册表中（底稿未同步？）")
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"研究底稿读取失败：{e}")

    # ── 输出 ──
    print(f"质检对象: {args.report}")
    print(f"字数: {wc}（要求 {args.min_words}-{args.max_words}）")
    print(f"引证: 正文引用 {len(cited_ids)} 条 / 来源登记 {len(defined_ids)} 条")
    for e in errors:
        print(f"[ERROR] {e}")
    for w in warnings:
        print(f"[WARN]  {w}")
    print(f"\n结果: {'❌ 未通过' if errors else '✅ 通过'}（{len(errors)} ERROR / {len(warnings)} WARN）")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
