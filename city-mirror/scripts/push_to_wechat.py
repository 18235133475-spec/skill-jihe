#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号 HTML 预排版 → 微信公众号草稿箱（一键推送）。

用法:
    python3 push_to_wechat.py 预排版.html [选项]

选项:
    --title  "标题"      文章标题（默认取 HTML 的 <title> 或第一个 <h1>，≤64 字）
    --author "作者"      作者署名（≤8 字）
    --digest "摘要"      摘要（≤120 字，留空则微信自动取正文前 54 字）
    --cover  封面图路径   封面图（默认取文章第一张图；微信要求必须有封面）
    --source-url URL     "阅读原文"链接（可选）
    --dry-run            只做图片上传与 HTML 转换，不推送草稿（自查用）

凭据配置（二选一，不写进代码、不进仓库）:
    1. 配置文件 ~/.config/city-mirror/wechat.json:
       {"appid": "wx...", "secret": "..."}
    2. 环境变量: WECHAT_APPID / WECHAT_SECRET

依赖: 仅标准库。图片超 1MB 时需要 Pillow 自动压缩（pip install Pillow），
      未装 Pillow 且图片超限会报错并提示手动压缩。

前置条件（必读，否则接口会报错）:
    - 公众号须为「已认证服务号」或「已认证订阅号」，个人订阅号无草稿箱 API 权限；
    - 服务器出口 IP 必须加入公众号后台白名单：
      设置与开发 → 基本配置 → IP 白名单（查本机出口 IP: curl ifconfig.me）；
    - AppSecret 在「基本配置」页重置获取，只显示一次，请妥善保存。

微信侧渲染差异（预期内，不影响阅读）:
    - 字体被强制为系统字体，自定义 font-family 会被忽略；
    - <style> 标签会被过滤，故 HTML 必须全部用 inline style（本 skill 预排版已满足）；
    - 图片宽度由微信自适应，与本地预览可能有几像素差异。
    推送后在公众号后台「草稿箱」用手机预览确认一次。
"""
import argparse
import hashlib
import html as html_mod
import json
import mimetypes
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import uuid

API = "https://api.weixin.qq.com/cgi-bin"
CONFIG_PATH = os.path.expanduser("~/.config/city-mirror/wechat.json")
TOKEN_CACHE = os.path.expanduser("~/.config/city-mirror/.token_cache.json")
CONTENT_IMG_LIMIT = 1024 * 1024      # media/uploadimg 单图上限 1MB
MATERIAL_IMG_LIMIT = 10 * 1024 * 1024  # 永久素材（封面）上限 10MB


# ---------- 基础工具 ----------

def die(msg):
    sys.exit(f"错误: {msg}")


def load_credentials():
    appid, secret = os.environ.get("WECHAT_APPID"), os.environ.get("WECHAT_SECRET")
    if appid and secret:
        return appid, secret
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        appid, secret = cfg.get("appid"), cfg.get("secret")
        if appid and secret:
            return appid, secret
    die(f"未找到凭据。请创建 {CONFIG_PATH}：\n"
        '  {"appid": "wx...", "secret": "..."}\n'
        "或设置环境变量 WECHAT_APPID / WECHAT_SECRET")


def api_post(url, data=None, headers=None):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_get(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_error(result, action):
    """微信接口错误码统一处理，常见错误给出可操作提示。"""
    if "errcode" in result and result["errcode"] != 0:
        code, msg = result["errcode"], result.get("errmsg", "")
        hints = {
            40164: "服务器 IP 不在白名单。到公众号后台 设置与开发 → 基本配置 → IP 白名单 添加本机出口 IP（curl ifconfig.me）",
            48001: "接口未授权。个人订阅号无草稿箱 API 权限，需已认证的服务号/订阅号",
            40001: "AppSecret 错误，或 access_token 已失效（已自动重试仍失败请检查凭据）",
            41005: "图片文件读取失败或为空",
            40007: "media_id 无效",
            45009: "接口调用超过频率限制，稍后再试",
        }
        hint = hints.get(code, "")
        die(f"{action}失败 [{code}] {msg}" + (f"\n提示: {hint}" if hint else ""))
    return result


# ---------- access_token ----------

def get_access_token(appid, secret, force=False):
    """获取 access_token，带本地缓存（有效期 7200s，提前 300s 过期）。"""
    if not force and os.path.exists(TOKEN_CACHE):
        try:
            with open(TOKEN_CACHE, encoding="utf-8") as f:
                cache = json.load(f)
            if cache.get("appid") == appid and cache.get("expires_at", 0) > time.time():
                return cache["token"]
        except (json.JSONDecodeError, OSError):
            pass

    url = f"{API}/token?grant_type=client_credential&appid={appid}&secret={secret}"
    result = check_error(api_get(url), "获取 access_token")
    token = result["access_token"]

    os.makedirs(os.path.dirname(TOKEN_CACHE), exist_ok=True)
    with open(TOKEN_CACHE, "w", encoding="utf-8") as f:
        json.dump({"appid": appid, "token": token,
                   "expires_at": time.time() + result.get("expires_in", 7200) - 300}, f)
    os.chmod(TOKEN_CACHE, 0o600)
    return token


# ---------- 图片处理 ----------

def compress_if_needed(path, limit):
    """图片超限时用 Pillow 压缩，返回实际使用的路径（可能是临时文件）。"""
    size = os.path.getsize(path)
    if size <= limit:
        return path, None

    try:
        from PIL import Image
    except ImportError:
        die(f"图片 {os.path.basename(path)} 为 {size/1024/1024:.1f}MB，"
            f"超过微信 {limit/1024/1024:.0f}MB 限制。\n"
            "请安装 Pillow 以自动压缩（pip install Pillow），或手动压缩后重试。")

    img = Image.open(path)
    if img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg

    tmp = os.path.join(os.path.dirname(path) or ".", f".wx_tmp_{uuid.uuid4().hex[:8]}.jpg")
    quality, scale = 85, 1.0
    while True:
        out = img if scale == 1.0 else img.resize(
            (int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        out.save(tmp, "JPEG", quality=quality, optimize=True)
        if os.path.getsize(tmp) <= limit:
            break
        if quality > 60:
            quality -= 10
        elif scale > 0.4:
            scale -= 0.15
        else:
            os.remove(tmp)
            die(f"图片 {os.path.basename(path)} 压缩后仍超限，请手动处理")
    print(f"  （已压缩 {size/1024/1024:.1f}MB → {os.path.getsize(tmp)/1024/1024:.1f}MB）")
    return tmp, tmp


def build_multipart(field_name, file_path):
    """手工构造 multipart/form-data（避免引入 requests 依赖）。"""
    boundary = f"----CityMirror{uuid.uuid4().hex}"
    filename = os.path.basename(file_path)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    with open(file_path, "rb") as f:
        content = f.read()

    body = b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"),
        f"Content-Type: {ctype}\r\n\r\n".encode(),
        content,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    return body, f"multipart/form-data; boundary={boundary}"


def upload_content_image(token, path):
    """正文内图片：media/uploadimg，返回微信 CDN url。不占用素材库配额。"""
    real_path, tmp = compress_if_needed(path, CONTENT_IMG_LIMIT)
    try:
        body, ctype = build_multipart("media", real_path)
        req = urllib.request.Request(
            f"{API}/media/uploadimg?access_token={token}",
            data=body, headers={"Content-Type": ctype}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        check_error(result, f"上传正文图片 {os.path.basename(path)}")
        return result["url"]
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def upload_cover_image(token, path):
    """封面图：material/add_material 永久素材，返回 thumb_media_id。占用素材库配额。"""
    real_path, tmp = compress_if_needed(path, MATERIAL_IMG_LIMIT)
    try:
        body, ctype = build_multipart("media", real_path)
        req = urllib.request.Request(
            f"{API}/material/add_material?access_token={token}&type=image",
            data=body, headers={"Content-Type": ctype}, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        check_error(result, f"上传封面图 {os.path.basename(path)}")
        return result["media_id"]
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


# ---------- HTML 处理 ----------

def extract_body(html):
    """取 <body> 内容；微信会过滤 html/head/body/style 标签，只接受正文片段。"""
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S | re.I)
    content = m.group(1) if m else html
    if re.search(r"<style[^>]*>", content, re.I):
        print("  警告: 正文含 <style> 标签，微信会过滤。请确认样式已全部写成 inline style。")
    return content.strip()


def extract_title(html):
    for pattern in (r"<title[^>]*>(.*?)</title>", r"<h1[^>]*>(.*?)</h1>"):
        m = re.search(pattern, html, re.S | re.I)
        if m:
            title = re.sub(r"<[^>]+>", "", m.group(1))
            return html_mod.unescape(title).strip()
    return ""


def collect_local_images(content, base_dir):
    """收集正文中的本地图片路径（跳过已是 http/data 的）。"""
    images = []
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.I):
        src = m.group(1)
        if src.startswith(("http://", "https://", "data:")):
            continue
        path = src if os.path.isabs(src) else os.path.join(base_dir, urllib.parse.unquote(src))
        if os.path.exists(path):
            images.append((src, os.path.normpath(path)))
        else:
            print(f"  警告: 图片不存在，跳过 → {src}")
    return images


def replace_images(content, url_map):
    """把本地 src 替换为微信 CDN url。"""
    for src, url in url_map.items():
        content = content.replace(f'src="{src}"', f'src="{url}"')
        content = content.replace(f"src='{src}'", f"src='{url}'")
    return content


def make_digest(content, limit=120):
    """摘要留空时微信会自动截取，此处仅在需要时生成一份纯文本摘要。"""
    text = re.sub(r"<[^>]+>", "", content)
    text = html_mod.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:limit]


# ---------- 草稿推送 ----------

def add_draft(token, article):
    result = api_post(f"{API}/draft/add?access_token={token}",
                      {"articles": [article]},
                      {"Content-Type": "application/json; charset=utf-8"})
    check_error(result, "推送草稿")
    return result["media_id"]


def main():
    ap = argparse.ArgumentParser(description="公众号 HTML → 微信草稿箱", add_help=True)
    ap.add_argument("html", help="HTML 预排版文件路径")
    ap.add_argument("--title", default="", help="文章标题（≤64 字）")
    ap.add_argument("--author", default="", help="作者署名（≤8 字）")
    ap.add_argument("--digest", default="", help="摘要（≤120 字）")
    ap.add_argument("--cover", default="", help="封面图路径（默认取正文第一张图）")
    ap.add_argument("--source-url", default="", help="「阅读原文」链接")
    ap.add_argument("--dry-run", action="store_true", help="只转换不推送")
    args = ap.parse_args()

    if not os.path.exists(args.html):
        die(f"HTML 文件不存在: {args.html}")

    with open(args.html, encoding="utf-8") as f:
        raw = f.read()

    base_dir = os.path.dirname(os.path.abspath(args.html))
    content = extract_body(raw)

    title = (args.title or extract_title(raw)).strip()
    if not title:
        die("未能确定标题，请用 --title 指定")
    if len(title) > 64:
        print(f"  警告: 标题 {len(title)} 字超过微信 64 字上限，已截断")
        title = title[:64]

    appid, secret = load_credentials()
    token = get_access_token(appid, secret)

    # 1) 上传正文图片
    images = collect_local_images(content, base_dir)
    print(f"发现本地图片 {len(images)} 张")
    url_map = {}
    for i, (src, path) in enumerate(images, 1):
        if path in url_map.values():
            continue
        print(f"[{i}/{len(images)}] 上传 {os.path.basename(path)}")
        url_map[src] = upload_content_image(token, path)
    content = replace_images(content, url_map)

    # 2) 封面图（微信必填）
    cover_path = args.cover
    if not cover_path and images:
        cover_path = images[0][1]
    if not cover_path:
        die("文章无图片且未指定 --cover。微信草稿必须有封面图。")
    if not os.path.exists(cover_path):
        die(f"封面图不存在: {cover_path}")

    if args.dry_run:
        out = os.path.join(base_dir, "_wechat_preview.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n[dry-run] 图片已上传，转换结果写入: {out}")
        print(f"[dry-run] 标题: {title}")
        print(f"[dry-run] 封面: {os.path.basename(cover_path)}")
        print("[dry-run] 未推送草稿。去掉 --dry-run 执行推送。")
        return

    print(f"上传封面图 {os.path.basename(cover_path)}")
    thumb_media_id = upload_cover_image(token, cover_path)

    # 3) 推送草稿
    article = {
        "title": title,
        "author": args.author[:8],
        "digest": (args.digest or make_digest(content))[:120],
        "content": content,
        "content_source_url": args.source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }
    media_id = add_draft(token, article)

    print("\n✓ 草稿推送成功")
    print(f"  标题: {title}")
    print(f"  草稿 media_id: {media_id}")
    print("  到公众号后台「草稿箱」查看，建议用手机预览确认渲染效果后再发布。")


if __name__ == "__main__":
    main()
