#!/usr/bin/env python3
"""
校园墙「孤儿文件」清理脚本

孤儿文件 = 上传目录里存在、但没有任何留言/评论引用的文件。
典型来源：留言被后台删除后，它带的图片/视频/音频仍留在 static/uploads；
          对应的缩略图也留在 static/tiny_files。

安全设计
  · 默认只统计并列出，不删除（先看清楚再动手）
  · 只处理 static/uploads 与 static/tiny_files，绝不碰 static/avatars、static/messages、.env 等
  · 默认跳过「最近 24 小时」内修改的文件，避免误删正在上传、尚未发布的文件
  · 只删普通文件，不递归删目录

用法（在 /www/wwwroot/default/backend/backend 目录下执行）
  python3 clean_orphans.py                # 预演：只列出，不删
  python3 clean_orphans.py --delete       # 真正删除孤儿文件
  python3 clean_orphans.py --delete --min-age-hours 72     # 只删 72 小时前的
  python3 clean_orphans.py --delete --chunks               # 顺带清理一天前的分片上传残留目录
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import time

# 防御：某些终端（尤其 Windows GBK 控制台）遇到特殊字符会直接抛 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'static', 'messages', 'messages.db')
UPLOADS = os.path.join(BASE, 'static', 'uploads')
TINY = os.path.join(BASE, 'static', 'tiny_files')
CHUNKS = os.path.join(BASE, 'static', 'chunks')

PREVIEW_COUNT = 20  # 预览时最多列出多少个文件


def human(size):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f"{size:.1f} {unit}" if unit != 'B' else f"{int(size)} B"
        size /= 1024


def collect_used(db_path):
    """收集所有被留言或评论引用的文件名"""
    used = set()
    if not os.path.exists(db_path):
        raise SystemExit(f"[X] 找不到留言库：{db_path}\n    请在 backend 目录下执行本脚本。")
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute('select data from messages').fetchall()
    finally:
        conn.close()

    for (raw,) in rows:
        try:
            info = json.loads(raw)
        except (TypeError, ValueError):
            continue
        for name in (info.get('files') or []):
            if isinstance(name, str) and name:
                used.add(name)
        for comment in (info.get('comments') or []):
            for name in (comment.get('files') or []):
                if isinstance(name, str) and name:
                    used.add(name)
    return used, len(rows)


def scan(folder, used, min_age_seconds):
    """返回 (保留数量, [(文件名, 大小), ...])"""
    if not os.path.isdir(folder):
        return 0, []
    kept, orphans = 0, []
    now = time.time()
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):      # 目录一律不碰
            continue
        if name in used:
            kept += 1
            continue
        try:
            if now - os.path.getmtime(path) < min_age_seconds:
                kept += 1                # 太新，可能正在上传，先留着
                continue
            orphans.append((name, os.path.getsize(path)))
        except OSError:
            kept += 1
    return kept, orphans


def report(label, folder, kept, orphans, do_delete):
    total = sum(size for _, size in orphans)
    print(f"\n== {label}  ({folder})")
    print(f"   保留 {kept} 个，孤儿 {len(orphans)} 个，可回收 {human(total)}")
    for name, size in orphans[:PREVIEW_COUNT]:
        print(f"     - {name}  ({human(size)})")
    if len(orphans) > PREVIEW_COUNT:
        print(f"     … 还有 {len(orphans) - PREVIEW_COUNT} 个未列出")

    if do_delete and orphans:
        removed, freed = 0, 0
        for name, size in orphans:
            try:
                os.remove(os.path.join(folder, name))
                removed += 1
                freed += size
            except OSError as error:
                print(f"     [!] 删除失败 {name}: {error}")
        print(f"   [OK] 已删除 {removed} 个，释放 {human(freed)}")
    return total


def clean_chunks(min_age_seconds, do_delete):
    if not os.path.isdir(CHUNKS):
        return
    now, stale = time.time(), []
    for name in sorted(os.listdir(CHUNKS)):
        path = os.path.join(CHUNKS, name)
        if not os.path.isdir(path):
            continue
        try:
            if now - os.path.getmtime(path) >= min_age_seconds:
                stale.append(path)
        except OSError:
            pass
    print(f"\n== 分片上传残留目录  ({CHUNKS})")
    print(f"   过期目录 {len(stale)} 个")
    for path in stale[:PREVIEW_COUNT]:
        print(f"     - {os.path.basename(path)}")
    if do_delete:
        for path in stale:
            try:
                shutil.rmtree(path)
                print(f"   [OK] 已删除 {os.path.basename(path)}")
            except OSError as error:
                print(f"   [!] 删除失败 {os.path.basename(path)}: {error}")


def main():
    parser = argparse.ArgumentParser(description='清理校园墙上传目录里的孤儿文件')
    parser.add_argument('--delete', action='store_true', help='真正删除（默认只统计）')
    parser.add_argument('--min-age-hours', type=float, default=24,
                        help='只处理修改时间早于 N 小时的文件（默认 24，防止误删正在上传的文件）')
    parser.add_argument('--chunks', action='store_true', help='顺带清理过期的分片上传目录')
    args = parser.parse_args()

    min_age_seconds = max(0.0, args.min_age_hours) * 3600
    print('=' * 64)
    print('校园墙孤儿文件清理' + ('（删除模式）' if args.delete else '（预演模式，不会删除任何文件）'))
    print(f'留言库 : {DB_PATH}')
    print(f'跳过最近 {args.min_age_hours:g} 小时内修改的文件')
    print('=' * 64)

    used, message_count = collect_used(DB_PATH)
    print(f'留言 {message_count} 条，被引用文件 {len(used)} 个')

    kept_u, orphan_u = scan(UPLOADS, used, min_age_seconds)
    kept_t, orphan_t = scan(TINY, used, min_age_seconds)

    total = report('上传原文件', UPLOADS, kept_u, orphan_u, args.delete)
    total += report('缩略图', TINY, kept_t, orphan_t, args.delete)

    if args.chunks:
        clean_chunks(min_age_seconds, args.delete)

    print('\n' + '=' * 64)
    if not args.delete:
        print(f'预演完成：共发现 {len(orphan_u) + len(orphan_t)} 个孤儿文件，可回收 {human(total)}')
        print('确认无误后执行：python3 clean_orphans.py --delete')
    else:
        print('清理完成 [OK]')
    print('=' * 64)


if __name__ == '__main__':
    main()
