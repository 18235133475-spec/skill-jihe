#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号正文配图：数据图表直出（自包含，无需外部 skill）。

覆盖城市号写作实际用得上的四种图型。**不许手写 matplotlib 代码绕开本脚本**——
版式约束（宽度、字号、换行、注脚位置、配色）全在这里，绕开一次就全部失效。
本脚本没有的图型，调 gzh-chart skill；两者都没有的，不出图，或先把图型补进本
脚本再出。（实战教训：跨平台调用时模型自行手写出图代码，出现标题堆叠、注脚
冗长、时间轴按时间比例排布留大片空白——三个毛病都源于绕开了版式收尾。）

依赖: pip install matplotlib

用法（作为库导入）:

    import sys; sys.path.insert(0, "<city-mirror>/scripts")
    from gen_chart import line, bar, barh, timeline

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

    # 横向条形（名称较长的排名/对比）。**传入顺序即自上而下的阅读顺序**
    barh(labels=["杭州", "太原", "济南"], y=[10000, 6000, 2500],
         title="部分城市公积金物业费提取年度上限",
         source="各地公积金中心公开文件",
         out="文章名_图3_各地上限.png", fmt="{:,.0f}",
         highlight="太原")                       # 主角上色，其余置灰

    # 时间轴（政策沿革、项目历程）。**默认等距，按事件序不按时间比例**
    timeline(events=[("1991", "上海首创公积金制度"),
                     ("2019", "国标落地，物业费被排除"),
                     ("2025", "超20城重启物业费提取"),
                     ("2026", "立法纳入国令第844号")],
             title="物业费提取政策关键节点",
             source="《住房公积金管理条例》及公开报道",
             out="文章名_图4_政策沿革.png",
             highlight="2026")

公众号出图约定（内置，不必另行设置）:
    900px 宽 PNG、纯白底、中文字体自动注册、标题客观描述数据（不写观点）、
    口径来源注脚统一置于右下角小号灰字。

版式硬约束（超限直接报错，不静默截断）:
    - **标题 ≤60 全角字**，超 28 字自动按标点断行，断超两行自动降到 14pt。
      标题只描述数据内容，口径与解释归正文——写不下不是版式问题，是标题写错了；
    - **注脚 ≤48 全角字**，只写「数据来源：X、Y」。方法学口径（如"沈阳为 90㎡
      以上上限""扬州按 3 元/㎡·月换算"）**不写在图上**，归正文的「数据口径说明」
      ——那本就是发布版必留的五类口径之一。图上注脚塞不下就是塞错了地方；
    - 折线自动留顶部余量与左右边距，最高点数值标注不会顶到标题、末点不会出界。

配色（不自选颜色，用 highlight 表达重点）:
    单系列一律同一个蓝；传 highlight= 时主角砖红、其余置灰。
    颜色只用来编码「谁是主角」，不用来区分没有含义的并列项——十一根柱子十一种
    颜色，颜色不承载任何信息，只是噪音。
    highlight 接受标签字符串、下标整数，或二者的列表；未命中任何标签会报错。

数据纪律（红线，阶段十只留判断，细则在这里）:
    - 只用「可写事实清单」内的数据，不为出图编造；补全只填空，不改已有数据点；
    - 标题只描述数据内容，观点留在正文。

缺口画法（红线，补不到时按此画，不许实线直连）:
    中国官方统计公报常为图片版，补全失败是常态。此时不臆造、不插值：
    缺口段用 gaps= 画虚线，图上标「X—Y 数据未取得」，注脚写明"虚线段为数据
    缺口，非实测走势"，文末口径说明补一条。实线直连会让读者读成"这几年是
    线性变化"——那是用图表制造事实，比不出图更坏。

时间轴的排布（红线，默认等距）:
    scale="even"（默认）按事件序等距排布，时间间隔不参与排布。
    scale="time" 才按时间比例，且仅当「间隔本身是信息」时用（如"停摆了七年"）。
    比例模式下最大间隔超过中位间隔 3 倍时自动断轴并画折断标记——1991 到 2019
    之间没有事件，按比例就是大半张图的空白，读者读不到任何东西。
    （实战教训：跨平台手写的时间轴按比例排布，早期节点挤成一堆、中段全空。）

取值两条红线（与阶段七口径终核同源，此处只列出图时最易犯的两条）:
    1) 绝对值与增速不可互推。中国统计惯例是增速按可比口径、绝对值按当期
       口径，不是一套账。不许用「本年值÷(1+增速)」反推上年值。实战判例：
       太原 2025 年公报载社零 2365.53 亿、增长 4.7%，但 2024 年公报载
       1946.92 亿，二者实际差 21.5%。有官方发布值一律取发布值；官方从未
       发布过该年数值时才可反推，且须注脚标「据 X 年公报增速推算」并与
       实测值区分线型。
    2) 历史值会被修订。同一年份在不同年份公报里数值可能不同。实战判例：
       太原 2019 年社零，2019 年公报为 1952.81 亿，2020 年公报图5 已修订为
       1769.01 亿，差 184 亿。做法：优先取同一份公报内的连续序列（一份公报
       内部必然同口径）；必须跨公报拼接时以最新一份的历史值为准，并在口径
       说明注明"历史值经统计部门修订"。不许把不同年份公报的绝对值直接连成
       一条线。

数据补全的渠道阶梯（先查调研底稿「数据系列」节，多数情况直接取用；
不全时才走下面，补全搜索预算 ≤6 次，补到的须标来源并回写底稿）:
    1) 本级统计局的统计公报（主渠道）。公报正文常为 PNG 扫描图，但这不是
       障碍——把图片下载下来直接读即可。更关键的是公报内的图表通常直接给出
       近五年完整序列（如太原 2025 年公报「图4 2021—2025年社会消费品零售
       总额」一张图含 5 年数值＋增速），一张图解决整个补全；
    2) 业务主管部门的「运行情况」通报：社零找商务局、房产找住建局、工业找
       工信局，多为纯文字易提取。必须点进具体文章页——栏目页只有标题列表
       （实战教训：曾停在商务局栏目页误判"无数据"）；
    3) 直接搜数值：query 写「城市 + 年份 + 指标 + 亿元」，搜索引擎摘要常直接命中；
    4) 国家统计局「国家数据」（data.stats.gov.cn）分省分市年度数据，结构化可直接读；
    5) 政府工作报告：带上一年度主要指标，常被忽略的后门；
    6) 统计年鉴/公报转载站、权威媒体转述：最后手段，须两源交叉。

四种图型之外（热力图、小多图、堆叠面积等）调 gzh-chart skill，
它是可选增强，没装不影响上面四种图型出图。
"""
import os
import unicodedata

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ---------- 公众号出图约定 ----------

FIGSIZE = (9, 5.4)      # ×100 dpi = 900px 宽
DPI = 100

BASE = "#4C72B0"        # 单系列基准色
ACCENT = "#C0392B"      # 主角色（highlight 命中）
MUTED = "#B9B9B9"       # 配角灰
GREY = "#999999"
PALETTE = [BASE, "#DD8452", "#55A868", ACCENT, "#8172B3", "#937860"]  # 多系列折线用

# 版式硬约束（全角字为单位；实测 900px 宽下的溢出线：标题 @16pt 约 36 字、
# 注脚 @8pt 约 78 字。下面的上限都留了余量）
TITLE_LINE = 28         # 标题单行上限，超了换行
TITLE_MAX = 60          # 标题总长上限，超了报错
SOURCE_MAX = 48         # 注脚（用户传入部分）上限，超了报错
SOURCE_LINE = 60        # 注脚单行上限，超了换行

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


# ---------- 版式工具 ----------

_BREAK_AFTER = "，。；、）」》】：,;:)]｜| "


def _units(s):
    """文本宽度，以全角字为 1 单位。"""
    return sum(1.0 if unicodedata.east_asian_width(c) in "WFA" else 0.55
               for c in s)


def _wrap(s, limit):
    """按宽度换行，优先在标点后断开。"""
    lines, cur, w = [], "", 0.0
    for ch in s:
        cw = _units(ch)
        if w + cw > limit and cur:
            cut = len(cur)
            for i in range(len(cur) - 1, int(len(cur) * 0.5) - 1, -1):
                if cur[i] in _BREAK_AFTER:
                    cut = i + 1
                    break
            lines.append(cur[:cut].rstrip())
            cur = cur[cut:]
            w = _units(cur)
        cur += ch
        w += cw
    if cur:
        lines.append(cur.rstrip())
    return lines


def _wrap_even(s, limit):
    """按满行换行；只有当末行被挤成孤字（"…第844" / "号"）时才改为均分。

    先满行、后均分，是因为满行更容易落在标点上断开——一上来就均分，
    会把「无法开展」这类引号内的词从中间劈开。
    """
    u = _units(s)
    if u <= limit:
        return [s]
    lines = _wrap(s, limit)
    if _units(lines[-1]) > 1.5:
        return lines
    return _wrap(s, u / len(lines) + 0.5)


def _fit_title(title):
    """标题换行与降号。超总长上限报错——标题写太长是内容问题，不是版式问题。"""
    u = _units(title)
    if u > TITLE_MAX:
        raise ValueError(
            f"标题 {u:.0f} 全角字，超上限 {TITLE_MAX} 字：{title}\n"
            "图表标题只描述数据内容（画的是什么、哪个范围、什么时间），"
            "口径、解释、观点一律归正文。")
    if u <= TITLE_LINE:
        return title, 16
    lines = _wrap_even(title, TITLE_LINE)
    return "\n".join(lines), 16 if len(lines) <= 2 else 14


def _fit_source(source, note=""):
    """注脚换行。超上限报错——把口径写在图上是归位错误，不给静默通过。"""
    u = _units(source)
    if u > SOURCE_MAX:
        raise ValueError(
            f"注脚 {u:.0f} 全角字，超上限 {SOURCE_MAX} 字：{source}\n"
            "图上注脚只写「数据来源：X、Y」。方法学口径（换算方式、统计范围、"
            "不同对象的口径差异）归正文的「数据口径说明」——那是发布版必留的"
            "五类口径之一，写在图上读者既看不清也找不到。")
    text = f"数据来源：{source}"
    if note:
        text += f"　{note}"
    return _wrap(text, SOURCE_LINE)


def _colors(labels, highlight):
    """主角上色，其余置灰；不传 highlight 则单系列同色。"""
    n = len(labels)
    if highlight is None:
        return [BASE] * n
    wanted = highlight if isinstance(highlight, (list, tuple, set)) else [highlight]
    idx = set()
    for h in wanted:
        if isinstance(h, int) and not isinstance(h, bool):
            idx.add(h if h >= 0 else n + h)
        else:
            idx.update(i for i, lab in enumerate(labels) if str(lab) == str(h))
    if not idx:
        raise ValueError(f"highlight={highlight} 未命中任何标签：{list(labels)}")
    return [ACCENT if i in idx else MUTED for i in range(n)]


def _finish(fig, ax, title, ylabel, source, out, note=""):
    """统一收尾：标题、去边框、注脚、白底保存。"""
    text, fontsize = _fit_title(title)
    ax.set_title(text, fontsize=fontsize, fontweight="bold", pad=14)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    lines = _fit_source(source, note)
    fig.text(0.98, 0.02, "\n".join(lines), ha="right", va="bottom",
             fontsize=8, color=GREY, linespacing=1.5)
    fig.patch.set_facecolor("white")
    fig.tight_layout(rect=[0, 0.04 + 0.035 * len(lines), 1, 1])

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
            ax.plot(seg_x, seg_y, color=BASE, linewidth=2,
                    linestyle="--", alpha=0.55, zorder=4)
        else:
            ax.plot(seg_x, seg_y, color=BASE, linewidth=2.5, zorder=4)

    ax.scatter(x, y, color=BASE, s=70, zorder=5)
    for xi, yi in zip(x, y):
        ax.annotate(fmt.format(yi), (xi, yi), textcoords="offset points",
                    xytext=(0, 14), ha="center", fontsize=12,
                    fontweight="bold", color=BASE)

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
    # 左右留边距，末点数值标注不出界
    ax.margins(x=0.07)
    if ylim:
        ax.set_ylim(*ylim)
    else:
        # 顶部留余量，最高点的数值标注（+14pt）不会顶到标题
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi + (hi - lo) * 0.14)
    ax.grid(axis="y", alpha=0.3)

    note = "虚线段为数据缺口，非实测走势" if gaps else ""
    return _finish(fig, ax, title, ylabel, source, out, note)


def bar(labels, y, title, source, out, ylabel="", fmt="{:g}", highlight=None):
    """柱状图（少量对象或时间点的对比）。

    highlight: 主角标签或下标（可传列表）。命中的砖红，其余置灰；不传则同色。
    """
    labels, y = list(labels), list(y)
    colors = _colors(labels, highlight)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.bar(labels, y, color=colors, width=0.5,
                  edgecolor="white", linewidth=1.5)
    span = max(y) - min(0, min(y))
    for b, v, c in zip(bars, y, colors):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + span * 0.02,
                fmt.format(v), ha="center", va="bottom",
                fontsize=13, fontweight="bold",
                color=ACCENT if c == ACCENT else "#333333")
    ax.set_ylim(0, max(y) * 1.2)
    ax.grid(axis="y", alpha=0.3)
    return _finish(fig, ax, title, ylabel, source, out)


def barh(labels, y, title, source, out, fmt="{:g}", show_pct=False,
         highlight=None):
    """横向条形图（名称较长的排名或对比）。

    **传入顺序即自上而下的阅读顺序**——排名图把第一名传在最前面即可，
    不必自行倒序。（matplotlib 的 barh 默认把首项画在最底下，本函数已翻正。）
    """
    labels, y = list(labels), list(y)
    colors = _colors(labels, highlight)
    labels, y, colors = labels[::-1], y[::-1], colors[::-1]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    bars = ax.barh(labels, y, color=colors, height=0.45,
                   edgecolor="white", linewidth=1.5)
    total = sum(y) or 1
    for b, v, c in zip(bars, y, colors):
        txt = fmt.format(v) + (f"（{v / total * 100:.0f}%）" if show_pct else "")
        ax.text(b.get_width() + max(y) * 0.02,
                b.get_y() + b.get_height() / 2, txt,
                ha="left", va="center", fontsize=13, fontweight="bold",
                color=ACCENT if c == ACCENT else "#333333")
    ax.set_xlim(0, max(y) * 1.35)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", labelsize=12)
    for lab, c in zip(ax.get_yticklabels(), colors):
        if c == ACCENT:
            lab.set_color(ACCENT)
            lab.set_fontweight("bold")
    return _finish(fig, ax, title, "", source, out)


def timeline(events, title, source, out, scale="even", highlight=None,
             note=""):
    """时间轴（政策沿革、项目历程）。

    events: [(时点, 事件), ...]，按时间先后传入，上限 10 个。
            时点写成能一眼读懂的短串（"1991""2026.08""8月11日"）；
            事件一句话，超 11 全角字自动换行。
    scale : "even"（默认）按事件序等距排布，时间间隔不参与排布；
            "time" 按时间比例，仅当「间隔本身是信息」时才用（如"停摆七年"）。
            比例模式要求时点可转成数字，且最大间隔超中位间隔 3 倍时自动断轴。
    highlight: 主角时点或下标（可传列表），砖红加粗并加环。
    """
    events = [tuple(e) for e in events]
    if not 2 <= len(events) <= 10:
        raise ValueError(f"时间轴节点 {len(events)} 个，应在 2—10 之间。"
                         "超过 10 个必然互相挤压，拆成两张图或只留关键节点。")
    whens = [str(e[0]) for e in events]
    texts = [str(e[1]) for e in events]
    colors = _colors(whens, highlight)

    # ---- 位置 ----
    marks = []          # 需要画折断标记的位置
    if scale == "even":
        pos = list(range(len(events)))
    elif scale == "time":
        try:
            vals = [float(w) for w in whens]
        except ValueError:
            raise ValueError(
                f"scale='time' 要求时点可转成数字，当前为 {whens}。"
                "改用 scale='even'（等距），或把时点写成年份数字。")
        gaps = [b - a for a, b in zip(vals, vals[1:])]
        if min(gaps) <= 0:
            raise ValueError("scale='time' 要求时点严格递增。")
        med = sorted(gaps)[len(gaps) // 2]
        pos, cur = [0.0], 0.0
        for i, g in enumerate(gaps):
            if g > med * 3:                 # 断轴：压到中位间隔的 2 倍
                marks.append(cur + med)
                cur += med * 2
            else:
                cur += g
            pos.append(cur)
    else:
        raise ValueError(f"scale 只接受 'even' 或 'time'，收到 {scale!r}。")

    # ---- 画 ----
    fig, ax = plt.subplots(figsize=(9, 4.4))
    wrapped = ["\n".join(_wrap_even(t, 11)) for t in texts]
    span = pos[-1] - pos[0] or 1

    # 两端留够首尾标签的半宽，否则最左/最右的说明会出界（坐标区约容 62 个全角字）
    def _half(i):
        return max([_units(whens[i])]
                   + [_units(ln) for ln in wrapped[i].split("\n")]) / 2

    lu, ru = _half(0), _half(-1)
    total = span / max(0.35, 1 - (lu + ru) / 62)
    left, right = max(lu * total / 62, span * 0.06), max(ru * total / 62, span * 0.06)
    pad = span * 0.05
    ax.plot([pos[0] - pad, pos[-1] + pad], [0, 0],
            color="#D5D5D5", linewidth=3, solid_capstyle="round", zorder=1)

    for m in marks:                          # 折断标记：两道斜线
        for dx in (-span * 0.008, span * 0.008):
            ax.plot([m + dx - span * 0.006, m + dx + span * 0.006],
                    [-0.09, 0.09], color="white", linewidth=3, zorder=2)
            ax.plot([m + dx - span * 0.006, m + dx + span * 0.006],
                    [-0.09, 0.09], color="#BBBBBB", linewidth=1.2, zorder=3)

    for i, (p, when, c) in enumerate(zip(pos, whens, colors)):
        up = i % 2 == 0
        sign = 1 if up else -1
        va = "bottom" if up else "top"
        ax.plot([p, p], [0, sign * 0.22], color=c if c == ACCENT else "#C9C9C9",
                linewidth=1.4, zorder=3)
        if c == ACCENT:
            ax.scatter([p], [0], s=210, facecolor="none", edgecolor=ACCENT,
                       linewidth=1.4, zorder=4)
        ax.scatter([p], [0], s=80, color=c, zorder=5)
        ax.text(p, sign * 0.28, when, ha="center", va=va, fontsize=12,
                fontweight="bold", color=c if c == ACCENT else "#333333")
        ax.text(p, sign * 0.50, wrapped[i], ha="center", va=va,
                fontsize=10, color=ACCENT if c == ACCENT else "#555555",
                linespacing=1.45)

    ax.set_xlim(pos[0] - left, pos[-1] + right)
    ax.set_ylim(-1.05, 1.05)
    ax.axis("off")
    if marks and not note:
        note = "轴上折断标记处为无事件的长间隔，已压缩"
    if scale == "even" and not note:
        note = "节点等距排布，横向距离不代表时间长短"
    return _finish(fig, ax, title, "", source, out, note)


if __name__ == "__main__":
    import sys
    print(__doc__)
    print("字体注册结果:", plt.rcParams["font.family"])
    sys.exit(0)
