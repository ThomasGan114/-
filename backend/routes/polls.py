"""
投票相关路由（前缀 /api/polls）

数据存在 backend/polls.json（运行时数据，不入库），结构：
[
  {
    "id": "uuid",
    "title": "投票标题（纯文本，≤200 字）",
    "createdAt": "YYYY-MM-DD HH:mm:ss",
    "ended": false,
    "voters": { "approve": ["设备ID", ...], "oppose": ["设备ID", ...] }
  }
]

票数不单独存计数器，而是由 voters 列表长度推导，避免计数漂移；
同一设备（voter_id，前端存在 localStorage）在同一投票里只能投一次。
"""
import json
import os
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Request

router = APIRouter()

POLLS_FILE = 'polls.json'
TITLE_MAX_LENGTH = 200

# 发起投票的简单限流（内存实现，同一 IP 每分钟最多 5 条）
CREATE_WINDOW_SECONDS = 60
CREATE_MAX_PER_WINDOW = 5
_create_records: Dict[str, List[float]] = {}

_lock = threading.Lock()


# ==================== 存取 ====================

def _load_polls() -> List[dict]:
    if not os.path.exists(POLLS_FILE):
        return []
    try:
        with open(POLLS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_polls(polls: List[dict]) -> None:
    """先写临时文件再替换，避免写一半导致文件损坏"""
    tmp = POLLS_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(polls, f, ensure_ascii=False, indent=2)
    os.replace(tmp, POLLS_FILE)


def _voters_of(poll: dict) -> dict:
    voters = poll.get('voters')
    if not isinstance(voters, dict):
        voters = {}
        poll['voters'] = voters
    voters.setdefault('approve', [])
    voters.setdefault('oppose', [])
    return voters


def _to_public(poll: dict, voter_id: str = '') -> dict:
    """转成前端需要的结构（票数由 voters 列表长度推导）"""
    voters = _voters_of(poll)
    my_vote = None
    if voter_id:
        if voter_id in voters['approve']:
            my_vote = 'approve'
        elif voter_id in voters['oppose']:
            my_vote = 'oppose'
    return {
        'id': poll.get('id'),
        'title': poll.get('title', ''),
        'approve': len(voters['approve']),
        'oppose': len(voters['oppose']),
        'createdAt': poll.get('createdAt', ''),
        'ended': bool(poll.get('ended')),
        'myVote': my_vote,
    }


def _is_create_rate_limited(client_ip: str) -> bool:
    now = time.time()
    recent = [t for t in _create_records.get(client_ip, []) if now - t < CREATE_WINDOW_SECONDS]
    if len(recent) >= CREATE_MAX_PER_WINDOW:
        _create_records[client_ip] = recent
        return True
    recent.append(now)
    _create_records[client_ip] = recent
    return False


# ==================== 请求体解析 ====================

async def _read_body(request: Request) -> dict:
    """手动解析 JSON 请求体：字段缺失/格式不对时给出中文提示，而不是 FastAPI 的 422"""
    try:
        body = await request.json()
    except Exception:
        return {}
    return body if isinstance(body, dict) else {}


# ==================== 接口 ====================

@router.get('')
async def list_polls(voter_id: str = ''):
    """投票列表（带 voter_id 时返回该设备投过什么）"""
    with _lock:
        polls = _load_polls()
    polls.sort(key=lambda p: p.get('createdAt', ''), reverse=True)
    return {"success": True, "polls": [_to_public(p, voter_id) for p in polls]}


@router.post('')
async def create_poll(request: Request):
    """发起投票（纯文本内容）"""
    body = await _read_body(request)
    title = str(body.get('title') or '').strip()
    creator_id = str(body.get('creator_id') or '').strip()

    # 先校验再计限流，避免「手滑提交空内容」白白消耗配额
    if not title:
        return {"success": False, "error": "请输入投票内容"}
    if len(title) > TITLE_MAX_LENGTH:
        return {"success": False, "error": f"投票内容不能超过 {TITLE_MAX_LENGTH} 字"}

    client_ip = request.client.host if request.client else 'unknown'
    if _is_create_rate_limited(client_ip):
        return {"success": False, "error": f"发起过于频繁，请 {CREATE_WINDOW_SECONDS} 秒后再试"}

    poll = {
        'id': uuid.uuid4().hex,
        'title': title,
        'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ended': False,
        'creator': creator_id,
        'voters': {'approve': [], 'oppose': []},
    }

    with _lock:
        polls = _load_polls()
        polls.append(poll)
        _save_polls(polls)

    return {"success": True, "poll": _to_public(poll, creator_id)}


@router.post('/{poll_id}/vote')
async def vote_poll(poll_id: str, request: Request):
    """投票：approve（赞成）或 oppose（反对），同一设备只能投一次"""
    body = await _read_body(request)
    choice = str(body.get('choice') or '').strip()
    voter_id = str(body.get('voter_id') or '').strip()

    if choice not in ('approve', 'oppose'):
        return {"success": False, "error": "无效的投票选项"}
    if not voter_id:
        return {"success": False, "error": "缺少设备标识，无法投票"}

    with _lock:
        polls = _load_polls()
        poll = next((p for p in polls if p.get('id') == poll_id), None)
        if poll is None:
            return {"success": False, "error": "投票不存在"}

        voters = _voters_of(poll)
        if voter_id in voters['approve'] or voter_id in voters['oppose']:
            return {"success": False, "error": "你已经投过票了"}
        if poll.get('ended'):
            return {"success": False, "error": "该投票已结束"}

        voters[choice].append(voter_id)
        _save_polls(polls)

    return {"success": True, "poll": _to_public(poll, voter_id)}
