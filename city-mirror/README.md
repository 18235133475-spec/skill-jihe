# city-mirror

城市号选题路由与镜像写作法 — 一个用于写城市向公众号深度文的 Claude skill。

任何热点或素材先过**概念界定**与**选题评估**，强对照时以热点为"镜子"写本地深度文。

## 流程（十阶段）

```
① 概念界定（三类歧义检验）
② 选题评估（负面清单 + 打分卡 + 落差当事人测试）
③ 广撒网（认知地形图 + 素材地图）
④ 立意五步（拉交叉表 → 换问法 → 提炼 → 三测 → 产出）
⑤ 结构（四段追问试讲 + 按主线分节 + 单引擎）
⑥ 沿线深挖（素材预算制）
⑦ 核实锁清单（对账 + 可写事实清单）
⑧ 叙事成稿（定表达 → 写 → 扫 + 反对者版本进稿）
⑨ 双审（合规 + 主观性）
⑩ 交付（详细版/发布版 + 配图 + HTML 预排版 / 草稿箱推送 / PDF）
```

约束分三层：**红线必守 / 默认可关 / 工具即退役**。调研全程底稿落盘。

## 目录

| 路径 | 说明 |
|---|---|
| `SKILL.md` | 主文件，完整流程与纪律 |
| `CHANGELOG.md` | 变更日志：每版改了什么 |
| `AUDIT.md` | 实战审计台账：每篇文章里哪些规则真出了力（规则去留的证据） |
| `references/stages/` | 十个阶段文件，每个自带入口/出口/红线表头，改哪步开哪个 |
| `references/` | 底稿模板、叙事原则、样式样例、调研 Agent 提示词 |
| `scripts/` | 交付脚本（见下） |

## 脚本

### `scripts/push_to_wechat.py`

HTML 预排版 → 微信公众号草稿箱。零依赖（仅标准库；图片超 1MB 时需 Pillow 自动压缩）。

```bash
python3 scripts/push_to_wechat.py 预排版.html --dry-run
```

确认无误后去掉 `--dry-run` 正式推送。**只推草稿箱，不做群发**——发布动作由用户在后台手动完成。

**凭据配置**（不进仓库）：

```json
// ~/.config/city-mirror/wechat.json
{"appid": "wx...", "secret": "..."}
```

或用环境变量 `WECHAT_APPID` / `WECHAT_SECRET`。

**前置条件**：
- 公众号须为**已认证**服务号或订阅号（个人订阅号无草稿箱 API 权限，报 48001）
- 服务器出口 IP 须加入公众号后台白名单（设置与开发 → 基本配置 → IP 白名单，否则报 40164）

### `scripts/check_skill.py`

改完 skill 后跑一遍，检查八项一致性（悬空引用／孤儿文件／阶段接口对齐／表头完整／废止术语残留／版本同步／标题层级／体量看板）。

```bash
python3 scripts/check_skill.py
```

**建议的改稿流程**：

```bash
git checkout -b 改04立意                      # 开分支
vim references/stages/04-thesis.md            # 只改一个阶段
python3 scripts/check_skill.py                # 自检
git diff                                      # 看改了什么
```

改坏了 `git checkout .` 退回。

### `scripts/md_to_pdf.py`

成稿 Markdown → PDF（reportlab CID 中文字体，无需装字体）。

```bash
python3 scripts/md_to_pdf.py 输入.md 输出.pdf
```

### `scripts/gen_chart.py`

公众号正文配图直出（自包含，不依赖外部 skill）。中文字体注册、900px 宽 PNG、纯白底、口径注脚右下角均已内置。

```python
from gen_chart import line, bar, barh, timeline

# 折线用 x=；柱状与横条用 labels=（三个函数的第一个参数名不同，别类推）
line(x=[2019, 2022, 2023, 2024], y=[1952.81, 1761.40, 1912.88, 1946.92],
     title="太原社会消费品零售总额变化（2019—2024）", ylabel="社零总额（亿元）",
     source="太原市统计公报（各年）", out="图1.png",
     gaps=[(2019, 2022)], gap_note="2020—2021 数据未取得")  # 缺口画虚线

bar(labels=["2022年", "2023年", "2024年"], y=[39, 46, 43],
    title="太原万象城年销售额（2022—2024）", ylabel="销售额（亿元）",
    source="华润年报", out="图2.png", fmt="{:.0f}亿")

barh(labels=["杭州", "太原", "济南"], y=[10000, 6000, 2500],   # 传入顺序即自上而下
     title="部分城市公积金物业费提取年度上限",
     source="各地公积金中心公开文件", out="图3.png",
     fmt="{:,.0f}", highlight="太原")            # 主角上色，其余置灰

timeline(events=[("1991", "上海首创公积金制度"),
                 ("2019", "国标落地，物业费被排除"),
                 ("2026", "立法纳入国令第844号")],
         title="物业费提取政策关键节点",
         source="《住房公积金管理条例》及公开报道",
         out="图4.png", highlight="2026")        # 默认等距，不按时间比例
```

依赖 `matplotlib`。四种图型：`line`（时间序列）/ `bar`（柱状）/ `barh`（横向条形）/ `timeline`（时间轴）。

**出图一律走这个脚本，不要手写 matplotlib**——版式约束（900px 宽、字号、标题自动换行、注脚长度上限、主角高亮配色）都在脚本里，绕开就全部失效。

## 配套 skill（可选）

需要四种图型之外的图（热力图、小多图、堆叠面积等）时，调用同仓库的 [`gzh-chart`](../gzh-chart)。**不装不影响基础出图**。

## 安装

```bash
npx skills add 18235133475-spec/skill-jihe@city-mirror
```

出图能力已内置，无需其他 skill。只有要画热力图、小多图等进阶图型时才需另装：

```bash
npx skills add 18235133475-spec/skill-jihe@gzh-chart
```

## 许可

MIT
