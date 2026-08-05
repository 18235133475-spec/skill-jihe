---
name: gzh-chart
description: 公众号出图 Skill。为微信公众号文章制作可直接粘贴进正文的数据图表（趋势折线、对比柱状、排名条形、结构堆叠、分布直方图等），基于 Python（matplotlib/seaborn/plotly）。内置中文字体注册与公众号出图约定（900px 宽、字号下限、标题客观描述数据、口径来源注脚统一右下角）。当用户说"公众号出图""给文章配图表""把数据做成图""画个趋势图/对比图/排名图""数据可视化"时触发。也适用于用户丢来一篇文章或一组数据说"帮我配几张图"的场景。
user-invocable: false
---

# 公众号出图 Skill（gzh-chart）

面向微信公众号正文配图的数据可视化。图表选型指南、Python 代码模板（内置中文字体注册）、公众号出图约定、设计原则与无障碍注意事项。

本 skill 改自 anthropics/knowledge-work-plugins 的 data-visualization，在此基础上加入中文环境支持与公众号版式约定。

**默认输出规格**：除非用户另行指定，所有图表按下文「微信公众号出图约定」出图（900px 宽 PNG、纯白底、标题客观描述、口径来源注脚右下角）。

## Chart Selection Guide

### Choose by Data Relationship

| What You're Showing | Best Chart | Alternatives |
|---|---|---|
| **Trend over time** | Line chart | Area chart (if showing cumulative or composition) |
| **Comparison across categories** | Vertical bar chart | Horizontal bar (many categories), lollipop chart |
| **Ranking** | Horizontal bar chart | Dot plot, slope chart (comparing two periods) |
| **Part-to-whole composition** | Stacked bar chart | Treemap (hierarchical), waffle chart |
| **Composition over time** | Stacked area chart | 100% stacked bar (for proportion focus) |
| **Distribution** | Histogram | Box plot (comparing groups), violin plot, strip plot |
| **Correlation (2 variables)** | Scatter plot | Bubble chart (add 3rd variable as size) |
| **Correlation (many variables)** | Heatmap (correlation matrix) | Pair plot |
| **Geographic patterns** | Choropleth map ⚠️无内置模板 | Bubble map, hex map（均需自行实现） |
| **Flow / process** | Sankey diagram ⚠️无内置模板 | Funnel chart（需自行实现） |
| **Relationship network** | Network graph ⚠️无内置模板 | Chord diagram（需自行实现） |
| **Performance vs. target** | Bullet chart | Gauge (single KPI only) |
| **Multiple KPIs at once** | Small multiples | Dashboard with separate charts |

### When NOT to Use Certain Charts

- **Pie charts**: Avoid unless <6 categories and exact proportions matter less than rough comparison. Humans are bad at comparing angles. Use bar charts instead.
- **3D charts**: Never. They distort perception and add no information.
- **Dual-axis charts**: Use cautiously. They can mislead by implying correlation. Clearly label both axes if used.
- **Stacked bar (many categories)**: Hard to compare middle segments. Use small multiples or grouped bars instead.
- **Donut charts**: Slightly better than pie charts but same fundamental issues. Use for single KPI display at most.

## Python Visualization Code Patterns

### Setup and Style

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np

# Professional style setup
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'figure.figsize': (10, 6),
    'figure.dpi': 150,
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16,
})

# CJK font registration (Chinese/Japanese/Korean labels)
# matplotlib does not auto-discover macOS .ttc system fonts; register explicitly.
import os
import matplotlib.font_manager as fm
for _font_path in (
    '/System/Library/Fonts/Hiragino Sans GB.ttc',      # macOS
    '/System/Library/Fonts/PingFang.ttc',              # macOS (部分系统)
    '/System/Library/Fonts/STHeiti Medium.ttc',        # macOS 备用
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Linux
):
    if os.path.exists(_font_path):
        fm.fontManager.addfont(_font_path)
plt.rcParams['font.family'] = ['Hiragino Sans GB', 'PingFang SC', 'STHeiti',
                               'Noto Sans CJK SC', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  # 负号用 ASCII，避免中文缺字形

# Colorblind-friendly palettes
PALETTE_CATEGORICAL = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B3', '#937860']
PALETTE_SEQUENTIAL = 'YlOrRd'
PALETTE_DIVERGING = 'RdBu_r'
```

### Line Chart (Time Series)

```python
fig, ax = plt.subplots(figsize=(10, 6))

for label, group in df.groupby('category'):
    ax.plot(group['date'], group['value'], label=label, linewidth=2)

ax.set_title('Metric Trend by Category', fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Value')
ax.legend(loc='upper left', frameon=True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Format dates on x-axis
fig.autofmt_xdate()

plt.tight_layout()
plt.savefig('trend_chart.png', dpi=150, bbox_inches='tight')
```

### Bar Chart (Comparison)

```python
fig, ax = plt.subplots(figsize=(10, 6))

# Sort by value for easy reading
df_sorted = df.sort_values('metric', ascending=True)

bars = ax.barh(df_sorted['category'], df_sorted['metric'], color=PALETTE_CATEGORICAL[0])

# Add value labels
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2,
            f'{width:,.0f}', ha='left', va='center', fontsize=10)

ax.set_title('Metric by Category (Ranked)', fontweight='bold')
ax.set_xlabel('Metric Value')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('bar_chart.png', dpi=150, bbox_inches='tight')
```

### Histogram (Distribution)

```python
fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(df['value'], bins=30, color=PALETTE_CATEGORICAL[0], edgecolor='white', alpha=0.8)

# Add mean and median lines
mean_val = df['value'].mean()
median_val = df['value'].median()
ax.axvline(mean_val, color='red', linestyle='--', linewidth=1.5, label=f'Mean: {mean_val:,.1f}')
ax.axvline(median_val, color='green', linestyle='--', linewidth=1.5, label=f'Median: {median_val:,.1f}')

ax.set_title('Distribution of Values', fontweight='bold')
ax.set_xlabel('Value')
ax.set_ylabel('Frequency')
ax.legend()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('histogram.png', dpi=150, bbox_inches='tight')
```

### Heatmap

```python
fig, ax = plt.subplots(figsize=(10, 8))

# Pivot data for heatmap format
pivot = df.pivot_table(index='row_dim', columns='col_dim', values='metric', aggfunc='sum')

sns.heatmap(pivot, annot=True, fmt=',.0f', cmap='YlOrRd',
            linewidths=0.5, ax=ax, cbar_kws={'label': 'Metric Value'})

ax.set_title('Metric by Row Dimension and Column Dimension', fontweight='bold')
ax.set_xlabel('Column Dimension')
ax.set_ylabel('Row Dimension')

plt.tight_layout()
plt.savefig('heatmap.png', dpi=150, bbox_inches='tight')
```

### Small Multiples

```python
categories = df['category'].unique()
n_cats = len(categories)
n_cols = min(3, n_cats)
n_rows = (n_cats + n_cols - 1) // n_cols

fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows), sharex=True, sharey=True)
axes = axes.flatten() if n_cats > 1 else [axes]

for i, cat in enumerate(categories):
    ax = axes[i]
    subset = df[df['category'] == cat]
    ax.plot(subset['date'], subset['value'], color=PALETTE_CATEGORICAL[i % len(PALETTE_CATEGORICAL)])
    ax.set_title(cat, fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# Hide empty subplots
for j in range(i+1, len(axes)):
    axes[j].set_visible(False)

fig.suptitle('Trends by Category', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('small_multiples.png', dpi=150, bbox_inches='tight')
```

### Number Formatting Helpers

```python
def format_number(val, format_type='number'):
    """Format numbers for chart labels."""
    if format_type == 'currency':
        if abs(val) >= 1e9:
            return f'${val/1e9:.1f}B'
        elif abs(val) >= 1e6:
            return f'${val/1e6:.1f}M'
        elif abs(val) >= 1e3:
            return f'${val/1e3:.1f}K'
        else:
            return f'${val:,.0f}'
    elif format_type == 'percent':
        return f'{val:.1f}%'
    elif format_type == 'number':
        if abs(val) >= 1e9:
            return f'{val/1e9:.1f}B'
        elif abs(val) >= 1e6:
            return f'{val/1e6:.1f}M'
        elif abs(val) >= 1e3:
            return f'{val/1e3:.1f}K'
        else:
            return f'{val:,.0f}'
    return str(val)

# Usage with axis formatter
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format_number(x, 'currency')))
```

### 微信公众号出图约定（默认规格）

本 skill 的默认出图规格，微信公众号正文可直接复制粘贴：

- **宽度**：固定 900px（公众号正文安全宽度）。`figsize=(9, h)` 配 `dpi=100`；需要 2 倍清晰度时 `dpi=200`（显示尺寸不变，手机上更锐利）
- **高度**：宽图（趋势、时间轴、排名）540px，即 `figsize=(9, 5.4)`；方图（构成、分布）675px，即 `figsize=(9, 6.75)`；单图最高不超过 900px，避免手机端一屏放不下
- **字号下限**（900px 宽手机阅读场景）：标题 ≥16pt，轴标签 ≥11pt，数据标签 ≥10pt，来源注脚 8-9pt
- **背景**：纯白不透明。透明底在公众号夜间模式下会花
- **标题**：客观描述数据内容（如「2025年春运主要车站客流对比」「太原机场与铁路年度客流（2015-2025）」），不写观点句、不引用文章原句——观点交给正文表达
- **注脚**：口径与数据来源统一放在图外**右下角**，右对齐，8-9pt 灰色；单位标在轴上
- **格式**：PNG。注意 `bbox_inches='tight'` 会改变最终像素尺寸，需要精确 900px 宽时保存后用 `sips -g pixelWidth` 校验

### Interactive Charts with Plotly

注意：agent 无头环境下 `fig.show()` 无效，一律用 `fig.write_html()` 落盘交付；需要 PNG 时安装 `kaleido` 后用 `fig.write_image()`。

```python
import plotly.express as px
import plotly.graph_objects as go

# Simple interactive line chart
fig = px.line(df, x='date', y='value', color='category',
              title='Interactive Metric Trend',
              labels={'value': 'Metric Value', 'date': 'Date'})
fig.update_layout(hovermode='x unified')
fig.write_html('interactive_chart.html')  # 无头环境交付方式；fig.show() 仅本地桌面有效

# Interactive scatter with hover data
fig = px.scatter(df, x='metric_a', y='metric_b', color='category',
                 size='size_metric', hover_data=['name', 'detail_field'],
                 title='Correlation Analysis')
fig.write_html('scatter.html')  # 同上，用 write_html 替代 fig.show()
```

## Design Principles

### Color

- **Use color purposefully**: Color should encode data, not decorate
- **Highlight the story**: Use a bright accent color for the key insight; grey everything else
- **Sequential data**: Use a single-hue gradient (light to dark) for ordered values
- **Diverging data**: Use a two-hue gradient with neutral midpoint for data with a meaningful center
- **Categorical data**: Use distinct hues, maximum 6-8 before it gets confusing
- **Avoid red/green only**: 8% of men are red-green colorblind. Use blue/orange as primary pair

### Typography

- **Title states the insight**: "Revenue grew 23% YoY" beats "Revenue by Month"
- **Subtitle adds context**: Date range, filters applied, data source
- **Axis labels are readable**: Never rotated 90 degrees if avoidable. Shorten or wrap instead
- **Data labels add precision**: Use on key points, not every single bar
- **Annotation highlights**: Call out specific points with text annotations

### Layout

- **Reduce chart junk**: Remove gridlines, borders, backgrounds that don't carry information
- **Sort meaningfully**: Categories sorted by value (not alphabetically) unless there's a natural order (months, stages)
- **Appropriate aspect ratio**: Time series wider than tall (3:1 to 2:1); comparisons can be squarer
- **White space is good**: Don't cram charts together. Give each visualization room to breathe

### Accuracy

- **Bar charts start at zero**: Always. A bar from 95 to 100 exaggerates a 5% difference
- **Line charts can have non-zero baselines**: When the range of variation is meaningful
- **Consistent scales across panels**: When comparing multiple charts, use the same axis range
- **Show uncertainty**: Error bars, confidence intervals, or ranges when data is uncertain
- **Label your axes**: Never make the reader guess what the numbers mean

## Accessibility Considerations

### Color Blindness

- Never rely on color alone to distinguish data series
- Add pattern fills, different line styles (solid, dashed, dotted), or direct labels
- Test with a colorblind simulator (e.g., Coblis, Sim Daltonism)
- Use the colorblind-friendly palette: `sns.color_palette("colorblind")`

### Screen Readers

- Include alt text describing the chart's key finding
- Provide a data table alternative alongside the visualization
- Use semantic titles and labels

### General Accessibility

- Sufficient contrast between data elements and background
- Text size minimum 10pt for labels, 12pt for titles
- Avoid conveying information only through spatial position (add labels)
- Consider printing: does the chart work in black and white?

### Accessibility Checklist

Before sharing a visualization:
- [ ] Chart works without color (patterns, labels, or line styles differentiate series)
- [ ] Text is readable at standard zoom level
- [ ] Title describes the insight, not just the data
- [ ] Axes are labeled with units
- [ ] Legend is clear and positioned without obscuring data
- [ ] Data source and date range are noted
