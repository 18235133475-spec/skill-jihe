#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""city-mirror 一致性自检。改完 skill 跑一遍，几秒出结果。

用法：
    python3 scripts/check_skill.py          # 在 skill 根目录下运行

查七项（每一项都对应一次真实翻车）：
    1. 悬空引用      文中提到的文件是否都存在
    2. 孤儿文件      存在但没人引用的文件
    3. 接口对齐      阶段文件声明的入口/出口 vs SKILL.md 接口总表
    4. 阶段文件表头  九个阶段文件是否都有入口/出口/红线/拍板点四项
    5. 废止术语      改名后是否有残留（样式甲乙丙丁等）；CHANGELOG/AUDIT 为历史记录，豁免
    6. 版本同步      SKILL.md 版本行 vs CHANGELOG 最新条目
    7. 体量看板      常驻/按需各多少 token（非错误，仅提示）

退出码：0 全过；1 有错误（✗）；错误之外的提醒（!）不影响退出码。
"""
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

ERR, WARN = [], []


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def tokens(text):
    cjk = len(re.findall(r'[一-鿿]', text))
    return cjk + (len(text) - cjk) / 4


# 废止术语表：改名后应清零（新增改名时往这里加一行）
RETIRED = [
    (r'样式[甲乙丙丁](?!\s*[＝=])', '样式字母代号（v4.31 废止，改用描述性名称）'),
    (r'references/(structure|review|delivery)\.md', '旧 references 路径（已移入 stages/）'),
]


def check_dangling_and_orphan():
    """1&2：悬空引用 / 孤儿文件"""
    md = [p for p in glob.glob('*.md') if os.path.basename(p) not in ('CHANGELOG.md', 'AUDIT.md')]
    md += glob.glob('references/**/*.md', recursive=True)
    all_text = '\n'.join(read(p) for p in md)
    referenced = set()
    for m in re.finditer(r'`?((?:references/)?(?:stages/)?[\w\-./]+\.(?:md|py))`?', all_text):
        referenced.add(os.path.normpath(m.group(1)))

    existing = set(os.path.normpath(p) for p in
                   glob.glob('references/**/*.md', recursive=True) + glob.glob('scripts/*.py'))

    for r in sorted(referenced):
        if r.endswith(('.md', '.py')) and ('references/' in r or 'scripts/' in r):
            cands = {r, os.path.normpath('references/' + r), os.path.normpath('references/stages/' + os.path.basename(r))}
            if not (cands & existing):
                ERR.append(f'悬空引用：{r} 被引用但不存在')

    for e in sorted(existing):
        base = os.path.basename(e)
        if base not in all_text and e not in all_text:
            WARN.append(f'孤儿文件：{e} 存在但无人引用')


def check_interfaces():
    """3&4：阶段文件表头 + 与接口总表对齐"""
    skill = read('SKILL.md')
    rows = re.findall(r'^\|\s*[①②③④⑤⑥⑦⑧⑨][^|]*\|\s*`([^`]+)`\s*\|([^|]*)\|([^|]*)\|', skill, re.M)
    table = {os.path.basename(f.strip()): (i.strip(), o.strip()) for f, i, o in rows}

    files = sorted(glob.glob('references/stages/*.md'))
    if not files:
        ERR.append('接口：references/stages/ 下没有阶段文件')
        return
    for p in files:
        base = os.path.basename(p)
        t = read(p)
        for field in ['入口', '出口', '本阶段红线', '用户拍板点']:
            if f'**{field}**' not in t:
                ERR.append(f'表头缺项：{base} 缺「{field}」')
        if base not in table:
            ERR.append(f'接口：{base} 未出现在 SKILL.md 接口总表中')

    for f in table:
        if not os.path.exists(f'references/stages/{f}'):
            ERR.append(f'接口：总表列出 {f}，但文件不存在')


def check_retired():
    """5：废止术语残留"""
    for p in glob.glob('*.md') + glob.glob('references/**/*.md', recursive=True):
        if os.path.basename(p) in ('CHANGELOG.md', 'AUDIT.md'):
            continue  # 变更史与台账是历史记录，保留当时的称呼
        t = read(p)
        for pat, why in RETIRED:
            for m in re.finditer(pat, t):
                ctx = t[max(0, m.start() - 6):m.start() + 10].replace('\n', ' ')
                if '原样式' in ctx or '原「样式' in ctx:
                    continue
                ERR.append(f'废止术语：{p}:{t[:m.start()].count(chr(10))+1} 「{m.group(0)}」——{why}')


def check_version():
    """6：版本同步"""
    sv = re.search(r'^> 版本：v([\d.]+)', read('SKILL.md'), re.M)
    vs = re.findall(r'^## v([\d.]+)', read('CHANGELOG.md'), re.M)
    if not sv or not vs:
        ERR.append('版本：SKILL.md 版本行或 CHANGELOG 条目缺失')
        return
    key = lambda v: tuple(int(x) for x in v.split('.'))
    newest = max(vs, key=key)  # CHANGELOG 排序不严格，取最大版本号
    if sv.group(1) != newest:
        ERR.append(f'版本不同步：SKILL.md=v{sv.group(1)}，CHANGELOG 最大=v{newest}')


def board():
    """7：体量看板"""
    res = tokens(read('SKILL.md'))
    stages = {os.path.basename(p): tokens(read(p)) for p in sorted(glob.glob('references/stages/*.md'))}
    support = {os.path.basename(p): tokens(read(p)) for p in sorted(glob.glob('references/*.md'))}
    print(f'\n{"体量看板":22}{"tokens":>9}')
    print('─' * 34)
    print(f'  {"SKILL.md（常驻）":20}{res:>9,.0f}')
    for k, v in stages.items():
        print(f'    stages/{k:<24}{v:>7,.0f}')
    for k, v in support.items():
        print(f'    {k:<31}{v:>7,.0f}')
    print('─' * 34)
    print(f'  {"按需合计":20}{sum(stages.values())+sum(support.values()):>9,.0f}')


def main():
    check_dangling_and_orphan()
    check_interfaces()
    check_retired()
    check_version()

    print('=== city-mirror 一致性自检 ===')
    if ERR:
        print(f'\n✗ {len(ERR)} 处错误：')
        for e in ERR:
            print(f'  ✗ {e}')
    else:
        print('\n✓ 七项检查全过')
    if WARN:
        print(f'\n! {len(WARN)} 处提醒（不阻塞）：')
        for w in WARN:
            print(f'  ! {w}')
    board()
    return 1 if ERR else 0


if __name__ == '__main__':
    sys.exit(main())
