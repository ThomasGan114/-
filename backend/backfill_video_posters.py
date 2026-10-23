#!/usr/bin/env python3
"""
为已有视频补生成「第一帧预览图」

新上传的视频会在后台自动生成预览图（tools.making_tiny_files -> make_video_poster），
但上线前上传的视频没有。本脚本扫描留言库，给缺预览图的视频补上。

预览图规格与图片缩略图一致：高度 100px、等比宽度，JPEG，存于 static/tiny_files/<视频文件名>.jpg
前端约定：视频预览图 URL = /static/tiny_files/<视频文件名>.jpg

用法（在 /www/wwwroot/default/backend/backend 目录下执行）
  python3 backfill_video_posters.py            # 只统计缺多少，不生成
  python3 backfill_video_posters.py --apply    # 真正生成

前置条件：服务器已安装 ffmpeg（命令行能直接执行 ffmpeg -version）
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
TINY = os.path.join(BASE, 'static', 'tiny_files')

VIDEO_EXTS = {'.mp4', '.m4v', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.3gp', '.ts', '.mts'}


def collect_videos(db_path):
    """从留言库里收集所有视频文件名（留言 + 评论）"""
    videos = set()
    if not os.path.exists(db_path):
        raise SystemExit(f"[X] 找不到留言库：{db_path}\n    请在 backend 目录下执行本脚本。")

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute('select data from messages').fetchall()
    finally:
        conn.close()

    def take(names):
        for name in (names or []):
            if isinstance(name, str) and name:
                if os.path.splitext(name.lower())[1] in VIDEO_EXTS:
                    videos.add(name)

    for (raw,) in rows:
        try:
            info = json.loads(raw)
        except (TypeError, ValueError):
            continue
        take(info.get('files'))
        for comment in (info.get('comments') or []):
            take(comment.get('files'))
    return videos


def main():
    parser = argparse.ArgumentParser(description='为已有视频补生成第一帧预览图')
    parser.add_argument('--apply', action='store_true', help='真正生成（默认只统计）')
    parser.add_argument('--height', type=int, default=100, help='预览图高度，默认 100（与图片缩略图一致）')
    args = parser.parse_args()

    print('=' * 60)
    print('视频预览图补生成' + ('（执行模式）' if args.apply else '（预演模式，不会生成文件）'))
    print(f'留言库: {DB_PATH}')
    print('=' * 60)

    if shutil.which('ffmpeg') is None:
        raise SystemExit('[X] 没找到 ffmpeg，请先安装后再运行本脚本（能执行 ffmpeg -version 即可）')

    videos = sorted(collect_videos(DB_PATH))
    print(f'共发现视频 {len(videos)} 个')

    missing = []
    for name in videos:
        if not os.path.isfile(os.path.join(UPLOADS, name)):
            print(f'  [!] 原视频不存在，跳过: {name}')
            continue
        poster = os.path.join(TINY, name + '.jpg')
        if os.path.isfile(poster) and os.path.getsize(poster) > 0:
            continue
        missing.append(name)

    print(f'缺预览图 {len(missing)} 个')
    for name in missing:
        print(f'  - {name}')

    if not missing:
        print('\n无需处理 [OK]')
        return

    if not args.apply:
        print('\n预演结束。确认后执行：python3 backfill_video_posters.py --apply')
        return

    from tools import make_video_poster

    os.makedirs(TINY, exist_ok=True)
    ok = 0
    for index, name in enumerate(missing, 1):
        print(f'[{index}/{len(missing)}] {name} ... ', end='', flush=True)
        success = make_video_poster(
            os.path.join(UPLOADS, name),
            os.path.join(TINY, name + '.jpg'),
            height=args.height,
        )
        print('OK' if success else 'FAILED')
        if success:
            ok += 1

    print('\n' + '=' * 60)
    print(f'完成：成功 {ok} 个，失败 {len(missing) - ok} 个')
    print('=' * 60)


if __name__ == '__main__':
    main()
