#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号成稿 Markdown → PDF（reportlab，CID 中文字体，无需安装字体）。

用法: python md_to_pdf.py 输入.md 输出.pdf
依赖: pip install reportlab   （建议 venv：python3 -m venv .venv_pdf）

    python3 -m venv .venv_pdf
    .venv_pdf/bin/pip install reportlab
    .venv_pdf/bin/python scripts/md_to_pdf.py 输入.md 输出.pdf

排版规格：A4、封面页（主标题+副标题+分隔线）、## 章节分页、首行缩进、
页码、来源列表小字、长 URL 自动换行。
约定：第一个 `# ` 行为封面主标题、第二个 `# ` 行作封面副标题；`##` 章节自动分页。
生成后用 pdftoppm 抽查：无乱码、长 URL 无溢出。
"""
import re, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, PageBreak, HRFlowable)
from reportlab.lib.styles import ParagraphStyle

if len(sys.argv) != 3:
    sys.exit("用法: python md_to_pdf.py 输入.md 输出.pdf")
SRC, OUT = sys.argv[1], sys.argv[2]

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
F = "STSong-Light"
BLUE, GREY, DARK = HexColor("#1a5276"), HexColor("#7f8c8d"), HexColor("#2c3e50")

body = ParagraphStyle("body", fontName=F, fontSize=10.5, leading=18, textColor=DARK,
                      alignment=TA_JUSTIFY, firstLineIndent=21, spaceAfter=4*mm, wordWrap="CJK")
src_st = ParagraphStyle("src", parent=body, fontSize=8.5, leading=13.5,
                        firstLineIndent=0, spaceAfter=1.5*mm)
h2 = ParagraphStyle("h2", fontName=F, fontSize=15, leading=22, textColor=BLUE,
                    spaceAfter=2*mm, wordWrap="CJK")
quote = ParagraphStyle("quote", parent=body, firstLineIndent=0, fontSize=9.5,
                       textColor=HexColor("#5d6d7e"), backColor=HexColor("#f4f6f7"),
                       borderPadding=3*mm, leftIndent=2*mm, rightIndent=2*mm)
cover_t = ParagraphStyle("ct", fontName=F, fontSize=19.5, leading=32, textColor=BLUE, alignment=TA_CENTER)
cover_s = ParagraphStyle("cs", fontName=F, fontSize=12.5, leading=20, textColor=GREY, alignment=TA_CENTER)

def esc(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r'<font color="#1a5276">\1</font>', s)

lines = open(SRC, encoding="utf-8").read().splitlines()

# 文件开头的连续 H1：第一个为主标题，第二个（如有）作封面副标题（自动去掉「备选标题：」前缀）
title, subtitle = "", ""
idx = 0
for ln in lines:
    if ln.startswith("# "):
        text_h = ln[2:].strip()
        if not title:
            title = text_h
        elif not subtitle:
            subtitle = re.sub(r"^备选标题[:：]\s*", "", text_h)
        idx += 1
    elif ln.strip() == "":
        idx += 1
        if title:
            break
    else:
        break

blocks, cur = [], []
for ln in lines[idx:]:
    if ln.strip() == "":
        if cur: blocks.append(cur); cur = []
    elif ln.startswith("# "):
        continue  # 已处理过的标题行
    else:
        cur.append(ln)
if cur: blocks.append(cur)

cover = [Spacer(1, 62*mm), Paragraph(esc(title), cover_t), Spacer(1, 8*mm)]
if subtitle:
    cover += [Paragraph(esc(subtitle), cover_s), Spacer(1, 2*mm)]
cover += [Spacer(1, 8*mm),
          HRFlowable(width="55%", thickness=1.2, color=BLUE, hAlign="CENTER"),
          PageBreak()]

story = cover
first_h2 = True
for blk in blocks:
    head = blk[0]
    if head.startswith("## "):
        if not first_h2: story.append(PageBreak())
        first_h2 = False
        story.append(Paragraph(esc(head[3:].strip()), h2))
        story.append(HRFlowable(width="100%", thickness=1.2, color=BLUE, spaceAfter=5*mm))
        for ln in blk[1:]:
            story.append(Paragraph(esc(ln.strip()), body))
    elif head.startswith("### "):
        story.append(Paragraph(esc(head[4:].strip()),
                     ParagraphStyle("h3", parent=h2, fontSize=12.5, textColor=HexColor("#1e8449"), spaceBefore=4*mm)))
        for ln in blk[1:]:
            story.append(Paragraph(esc(ln.strip()), body))
    elif head.startswith("> "):
        story.append(Paragraph(esc(" ".join(x.lstrip("> ") for x in blk).strip()), quote))
        story.append(Spacer(1, 2*mm))
    elif head.startswith("---"):
        story.append(Spacer(1, 4*mm))
    elif head.startswith("- "):
        for ln in blk:
            story.append(Paragraph("- " + esc(ln[2:].strip()), src_st))
    elif head.startswith("〔"):
        for ln in blk:
            story.append(Paragraph(esc(ln.strip()), src_st))
    else:
        story.append(Paragraph(esc(" ".join(x.strip() for x in blk)), body))

def on_page(canv, doc):
    if doc.page > 1:
        canv.setFont(F, 8)
        canv.setFillColor(GREY)
        canv.drawCentredString(A4[0]/2, 10*mm, f"第 {doc.page} 页")

doc = BaseDocTemplate(OUT, pagesize=A4,
                      leftMargin=18*mm, rightMargin=18*mm, topMargin=20*mm, bottomMargin=18*mm,
                      title=title, author="公众号文章")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])
doc.build(story)
print("PDF built:", OUT)
