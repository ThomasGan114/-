#!/usr/bin/env python3
"""
把已上传的视频重封装为「faststart」（索引 moov 移到文件头）

作用：浏览器不用等整个文件下载完就能读到时长、拖动进度更跟手。
      `-c copy` 是无损重封装，不重新编码，画质不变、几秒完成。

只处理 mp4 / m4v；其它容器（mov / avi / mkv …）需要转码，改动文件名会影响留言引用，
所以脚本只把它们列出来，不自动处理。

用法（在 /www/wwwroot/default/backend/backend 目录下执行，务必用 venv 的 python）
  /www/wwwroot/default/backend/venv/bin/python optimize_existing_media.py
  /www/wwwroot/default/backend/venv/bin/python optimize_existing_media.py --apply
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

DB_PATH = os.path.join(BASE, 'static', 'messages', 'messages.db')
UPLOADS = os.path.join(BASE, 'static', 'uploads')

FASTSTART_EXTS = {'.mp4', '.m4v'}
OTHER_VIDEO_EXTS = {'.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.3gp', '.ts', '.mts'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.avif'}


def human(size):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f"{size:.1f} {unit}" if unit != 'B' else f"{int(size)} B"
        size /= 1024


def collect_files(db_path):
    """收集留言与评论里引用的所有文件名"""
    if not os.path.exists(db_path):
        raise SystemExit(f'[X] 找不到留言库：{db_path}\n    请在 backend 目录下执行本脚本。')
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute('select data from messages').fetchall()
    finally:
        conn.close()

    names = set()

    def take(items):
        for name in (items or []):
            if isinstance(name, str) and name:
                names.add(name)

    for (raw,) in rows:
        try:
            info = json.loads(raw)
        except (TypeError, ValueError):
            continue
        take(info.get('files'))
        for comment in (info.get('comments') or []):
            take(comment.get('files'))
    return names


def main():
    parser = argparse.ArgumentParser(description='把已上传的视频重封装为 faststart')
    parser.add_argument('--apply', action='store_true', help='真正执行（默认只统计）')
    parser.add_argument('--force', action='store_true', help='连已经是 faststart 的视频也重做一遍')
    args = parser.parse_args()

    print('=' * 64)
    print('视频 faststart 重封装' + ('（执行模式）' if args.apply else '（预演模式，不会改动文件）'))
    print(f'上传目录: {UPLOADS}')
    print('=' * 64)

    if shutil.which('ffmpeg') is None:
        raise SystemExit('[X] 没找到 ffmpeg，请先安装后再运行（能执行 ffmpeg -version 即可）')

    try:
        from tools import optimize_video_for_web, mp4_moov_is_front
    except ModuleNotFoundError as error:
        venv_python = os.path.join(os.path.dirname(os.path.dirname(BASE)), 'venv', 'bin', 'python')
        raise SystemExit(
            f'[X] 缺少依赖模块：{error.name}\n'
            f'    请改用 venv 的 python 运行本脚本：\n'
            f'    {venv_python} optimize_existing_media.py'
        )

    names = collect_files(DB_PATH)
    faststart_targets = []
    other_videos = []
    images = 0
    missing = []

    for name in sorted(names):
        ext = os.path.splitext(name.lower())[1]
        path = os.path.join(UPLOADS, name)
        if not os.path.isfile(path):
            missing.append(name)
            continue
        if ext in IMAGE_EXTS:
            images += 1
            continue
        if ext in FASTSTART_EXTS:
            already = mp4_moov_is_front(path)
            faststart_targets.append((name, os.path.getsize(path), already))
            continue
        if ext in OTHER_VIDEO_EXTS:
            other_videos.append(name)

    print(f'引用文件共 {len(names)} 个：图片 {images} 个（无需处理）、mp4/m4v {len(faststart_targets)} 个、其它视频 {len(other_videos)} 个、缺失 {len(missing)} 个')

    todo = []
    for name, size, already in faststart_targets:
        if already is True and not args.force:
            continue
        todo.append((name, size, already))

    print(f'\n需要重封装 {len(todo)} 个：')
    for name, size, already in todo:
        flag = '已faststart(强制重做)' if already is True else ('索引在尾部' if already is False else '无法判断')
        print(f'  - [{flag}] {name}  ({human(size)})')

    if other_videos:
        print(f'\n[!] 以下 {len(other_videos)} 个非 mp4 视频需要转码才能 faststart，脚本不会自动处理：')
        for name in other_videos:
            print(f'  - {name}')
        print('    （转码会改变文件名并影响留言引用，需要的话单独做数据迁移）')

    if not todo:
        print('\n无需处理 [OK]')
        return

    if not args.apply:
        print('\n预演结束。确认后执行：')
        print('  /www/wwwroot/default/backend/venv/bin/python optimize_existing_media.py --apply')
        return

    ok = 0
    for index, (name, size, _already) in enumerate(todo, 1):
        path = os.path.join(UPLOADS, name)
        print(f'[{index}/{len(todo)}] {name} ({human(size)}) ... ', end='', flush=True)
        success = optimize_video_for_web(path)
        if success:
            after = os.path.getsize(path)
            front = mp4_moov_is_front(path)
            print(f'OK  {human(size)} -> {human(after)}  索引在头部: {front}')
            ok += 1
        else:
            print('FAILED')

    print('\n' + '=' * 64)
    print(f'完成：成功 {ok} 个，失败 {len(todo) - ok} 个')
    print('=' * 64)


if __name__ == '__main__':
    main()
