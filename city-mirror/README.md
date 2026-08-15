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
| `CHANGELOG.md` | 变更日志，含实战审计台账 |
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

### `scripts/md_to_pdf.py`

成稿 Markdown → PDF（reportlab CID 中文字体，无需装字体）。

```bash
python3 scripts/md_to_pdf.py 输入.md 输出.pdf
```

## 配套 skill

配图环节调用同仓库的 [`gzh-chart`](../gzh-chart) 生成数据图表（900px 宽 PNG，公众号规格）。

## 安装

```bash
npx skills add 18235133475-spec/skill-jihe@city-mirror
```

配套的 gzh-chart 一并装上：

```bash
npx skills add 18235133475-spec/skill-jihe@gzh-chart
```

## 许可

MIT
