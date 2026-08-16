# city-mirror

城市号选题路由与镜像写作法 — 一个用于写城市向公众号深度文的 Claude skill。

任何热点或素材先过**概念界定**与**选题评估**，强对照时以热点为"镜子"写本地深度文。

## 流程（九阶段）

```
① 概念界定（双向检验）
② 选题评估（打分卡 + 落差当事人测试）
③ 广撒网（认知地形图 + 素材地图）
④ 立意五步（拉交叉表 → 换问法 → 提炼 → 三测 → 产出）
⑤ 结构（五线试讲定线 + 两轴四样式 + 按主线分节）
⑥ 沿线深挖（素材预算制）
⑦ 核实锁清单（对账 + 可写事实清单）
⑧ 叙事成稿（两轮写扫 + 节内四件事 + 反对者版本进稿）
⑨ 双审 + 交付（HTML 预排版 / 草稿箱推送 / PDF）
```

约束分三层：**红线必守 / 默认可关 / 工具即退役**。调研全程底稿落盘。

## 目录

| 路径 | 说明 |
|---|---|
| `SKILL.md` | 主文件，完整流程与纪律 |
| `CHANGELOG.md` | 变更日志：每版改了什么 |
| `AUDIT.md` | 实战审计台账：每篇文章里哪些规则真出了力（规则去留的证据） |
| `references/stages/` | 九个阶段文件，每个自带入口/出口/红线表头，改哪步开哪个 |
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

改完 skill 后跑一遍，检查七项一致性（悬空引用／孤儿文件／阶段接口对齐／表头完整／废止术语残留／版本同步／体量看板）。

```bash
python3 scripts/check_skill.py
```

**建议的改稿流程**：

```bash
git checkout -b 改03立意                      # 开分支
vim references/stages/03-thesis.md            # 只改一个阶段
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
from gen_chart import line, bar, barh

line(x=[2019, 2022, 2023, 2024], y=[1952.81, 1761.40, 1912.88, 1946.92],
     title="太原社会消费品零售总额变化（2019—2024）", ylabel="社零总额（亿元）",
     source="太原市统计公报（各年）", out="图1.png",
     gaps=[(2019, 2022)], gap_note="2020—2021 数据未取得")  # 缺口画虚线
```

依赖 `matplotlib`。三种图型：`line`（时间序列）/ `bar`（柱状）/ `barh`（横向条形）。

## 配套 skill（可选）

需要三种图型之外的图（热力图、小多图、堆叠面积等）时，调用同仓库的 [`gzh-chart`](../gzh-chart)。**不装不影响基础出图**。

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
