#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号正文配图：数据图表直出（自包含，无需外部 skill）。

覆盖城市号写作实际用得上的三种图型；更复杂的图型（热力图、小多图、堆叠面积等）
再调 gzh-chart skill。

依赖: pip install matplotlib

用法（作为库导入）:

    import sys; sys.path.insert(0, "<city-mirror>/scripts")
    from gen_chart import line, bar, barh

    # 折线（时间序列）；gaps 标出数据缺口段，画成虚线并加标注
    line(x=[2019, 2022, 2023, 2024],
         y=[1952.81, 1761.40, 1912.88, 1946.92],
         title="太原社会消费品零售总额变化（2019—2024）",
         ylabel="社零总额（亿元）",
         source="太原市统计公报（各年）",
         out="文章名_图1_社零走势.png",
         gaps=[(2019, 2022)],                    # 该段无实测数据
         gap_note="2020—2021 数据未取得",
         fmt="{:.0f}亿")

    # 柱状（少量对象/时间点对比）
    bar(labels=["2022年", "2023年", "2024年"], y=[39, 46, 43],
        title="太原万象城年销售额（2022—2024）", ylabel="销售额（亿元）",
        source="华润年报 / 晋商俱乐部（2025.12）",
        out="文章名_图2_年销售额.png", fmt="{:.0f}亿")

    # 横向条形（名称较长的排名/对比）
    barh(labels=["商业部分", "住宅及其他"], y=[45, 65],
         title="项目总投资构成（约110亿元）",
         source="太原楼评 / 赢商网",
         out="文章名_图3_投资构成.png", fmt="{:.0f}亿元")

公众号出图约定（内置，不必另行设置）:
    900px 宽 PNG、纯白底、中文字体自动注册、标题客观描述数据（不写观点）、
    口径来源注脚统一置于右下角小号灰字。

数据纪律（见 SKILL.md ⑨配图）:
    - 只用可写事实清单内的数据，不为出图编造；
    - 时间序列有缺口时必须用 gaps 标出——实线直连会被读成"线性变化"，
      那是用图表制造事实；
    - 标题只描述数据内容，观点留在正文。
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ---------- 公众号出图约定 ----------

FIGSIZE = (9, 5.4)      # ×100 dpi = 900px 宽
DPI = 100
PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860"]
GREY = "#999999"

_CJK_FONTS = (
    "/System/Library/Fonts/Hiragino Sans GB.ttc",     # macOS
    "/System/Library/Fonts/PingFang.ttc",             # macOS
    "/System/Library/Fonts/STHeiti Medium.ttc",       # macOS
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",   # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msyh.ttc",                      # Windows
)


def _register_fonts():
    """注册系统中文字体，避免中文渲染成方块。"""
    names = []
    for path in _CJK_FONTS:
        if os.path.exists(path):
            try:
                fm.fontManager.addfont(path)
                names.append(fm.FontProperties(fname=path).get_name())
            except Exception:
                continue
    plt.rcParams["font.family"] = names + ["sans-serif"] if names else ["sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False
    if not names:
        print("警告: 未找到中文字体，中文可能显示为方块。"
              "Linux 可装 fonts-wqy-zenhei 或 Noto CJK。")
    return names


_register_fonts()


def _finish(fig, ax, title, ylabel, source, out):
    """统一收尾：标题、去边框、注脚、白底保存。"""
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    fig.text(0.98, 0.02, f"数据来源：{source}", ha="right", va="bottom",
             fontsize=8, color=GREY, style="italic")
    fig.patch.set_facecolor("white")
    fig.tight_layout(rect=[0, 0.05, 1, 1])

    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    # 不用 bbox_inches="tight"——它会裁掉边距，导致实际宽度小于约定的 900px
    fig.savefig(out, dpi=DPI, facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"saved: {out}")
    return out


# ---------- 图型 ----------

def line(x, y, title, source, out, ylabel="", fmt="{:g}",
         gaps=None, gap_note="数据未取得", ylim=None):
    """折线图（时间序列）。

    gaps: [(x起, x止), ...] 该区间无实测数据，画虚线并标注——不许实线直连。
    """
    gaps = gaps or []
    fig, ax = plt.subplots(figsize=FIGSIZE)

    def in_gap(a, b):
        return any(a == g0 and b == g1 for g0, g1 in gaps)

    # 逐段画：缺口段虚线，已知段实线
    for i in range(len(x) - 1):
        seg_x, seg_y = x[i:i + 2], y[i:i + 2]
        if in_gap(x[i], x[i + 1]):
            ax.plot(seg_x, seg_y, color=PALETTE[0], linewidth=2,
                    linestyle="--", alpha=0.55, zorder=4)
        else:
            ax.plot(seg_x, seg_y, color=PALETTE[0], linewidth=2.5, zorder=4)

    ax.scatter(x, y, color=PALETTE[0], s=70, zorder=5)
    for xi, yi in zip(x, y):
        ax.annotate(fmt.format(yi), (xi, yi), textcoords="offset points",
                    xytext=(0, 14), ha="center", fontsize=12,
                    fontweight="bold", color=PALETTE[0])

    # 缺口标注
    for g0, g1 in gaps:
        try:
            i0, i1 = x.index(g0), x.index(g1)
        except ValueError:
            continue
        ax.annotate(gap_note, xy=((g0 + g1) / 2, (y[i0] + y[i1]) / 2),
                    ha="center", va="center", fontsize=10, color=GREY,
                    bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                              edgecolor="#dddddd", linewidth=0.8))

    ax.set_xticks(x)
    ax.set_xticklabels([f"{v}年" if isinstance(v, int) else str(v) for v in x],
                       fontsize=11)
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(axis="y", alpha=0.3)

    if gaps:
        source += "  虚线段为数据缺口，非实测走势"
    return _finish(fig, ax, title, ylabel, source, out)


def bar(labels, y, title, source, out, ylabel="", fmt="{:g}"):
    """柱状图（少量对象或时间点的对比）。"""
    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.bar(labels, y, color=PALETTE[:len(labels)] * 3, width=0.5,
                  edgecolor="white", linewidth=1.5)
    span = max(y) - min(0, min(y))
    for b, v in zip(bars, y):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + span * 0.02,
                fmt.format(v), ha="center", va="bottom",
                fontsize=13, fontweight="bold")
    ax.set_ylim(0, max(y) * 1.2)
    ax.grid(axis="y", alpha=0.3)
    return _finish(fig, ax, title, ylabel, source, out)


def barh(labels, y, title, source, out, fmt="{:g}", show_pct=False):
    """横向条形图（名称较长的排名或对比）。"""
    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.barh(labels, y, color=PALETTE[:len(labels)] * 3, height=0.45,
                   edgecolor="white", linewidth=1.5)
    total = sum(y) or 1
    for b, v in zip(bars, y):
        txt = fmt.format(v) + (f"（{v / total * 100:.0f}%）" if show_pct else "")
        ax.text(b.get_width() + max(y) * 0.02,
                b.get_y() + b.get_height() / 2, txt,
                ha="left", va="center", fontsize=13, fontweight="bold")
    ax.set_xlim(0, max(y) * 1.35)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", labelsize=12)
    return _finish(fig, ax, title, "", source, out)


if __name__ == "__main__":
    import sys
    print(__doc__)
    print("字体注册结果:", plt.rcParams["font.family"])
    sys.exit(0)
