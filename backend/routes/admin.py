"""
管理员相关路由
"""
import os
import json
import uuid
import re
import hmac
import time
import shutil
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import APIRouter, Request, Form, File, UploadFile, Depends, HTTPException, Cookie
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse

from config import get_settings
from tools import log_admin_data, is_image_file, is_video_file, get_file_extension, making_tiny_files
from database import Database
from deps import get_message_manager

settings = get_settings()
router = APIRouter()

# 线程池
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=70)


def _safe_equal(a: str, b: str) -> bool:
    """定长时间比较，避免时序侧信道；用 bytes 兼容非 ASCII 密码"""
    return hmac.compare_digest(str(a).encode('utf-8'), str(b).encode('utf-8'))


def verify_admin(admin_name: str, admin_password: str) -> bool:
    """验证管理员账号密码

    密码优先取 .env 里的 ADMIN_PASSWORD（.env 不入库）；
    没有配置时才回退到 managers.json 的旧行为，并在日志里提示风险。
    空密码一律拒绝，避免 managers.json 里留空后被空密码登录。
    """
    if not admin_name or not admin_password:
        return False

    env_user = (settings.ADMIN_USERNAME or 'admin').strip()
    env_password = (settings.ADMIN_PASSWORD or '').strip()
    if env_password:
        return _safe_equal(admin_name, env_user) and _safe_equal(admin_password, env_password)

    # ---- 兼容旧配置：managers.json ----
    if not os.path.exists('managers.json'):
        return False
    try:
        with open('managers.json', 'r', encoding='utf-8') as f:
            managers_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    legacy_password = (managers_data.get(admin_name) or {}).get('password') or ''
    if not legacy_password:
        return False
    if _safe_equal(admin_password, legacy_password):
        print('[警告] 管理员密码来自 managers.json —— 建议在 backend/.env 里设置 ADMIN_PASSWORD')
        return True
    return False


def get_admin_user_permissions(admin_name: str) -> list:
    """获取管理员权限"""
    if not os.path.exists('managers.json'):
        return []
    with open('managers.json', 'r', encoding='utf-8') as f:
        managers_data = json.load(f)
    return managers_data.get(admin_name, {}).get('permissions', [])

def check_permission(permissions: list, name: str) -> bool:
    """检查管理员是否有指定权限"""
    return any(perm['name'] == name for perm in permissions)

def get_approved_ids() -> list:
    """获取已审核的消息ID"""
    if not os.path.exists('manage_message.json'):
        return []
    with open('manage_message.json', 'r', encoding='utf-8') as f:
        manage_data = json.load(f)
    ids = manage_data.get('approved', {}).get('lg', [])
    return [int(id['id']) for id in ids]


def get_admin_session(request: Request) -> tuple:
    """从请求中获取管理员会话信息"""
    admin_user = request.cookies.get('admin_user', '')
    admin_password = request.cookies.get('admin_password', '')
    return admin_user, admin_password

@router.get("/verify")
async def verify_admin_login(request: Request):
    """验证管理员登录"""
    admin_user, admin_password = get_admin_session(request)
    if verify_admin(admin_user, admin_password):
        return JSONResponse(content={"success": True})
    else:
        return JSONResponse(content={"success": False, "error": "未登录或登录过期"})

# ==================== 登录频率限制（内存实现，不引入额外依赖） ====================
LOGIN_WINDOW_SECONDS = 60   # 统计窗口（秒）
LOGIN_MAX_ATTEMPTS = 10     # 同一 IP 在窗口内允许的登录尝试次数
_login_attempts: Dict[str, List[float]] = {}


def is_login_rate_limited(client_ip: str) -> bool:
    """同一 IP 在窗口内尝试次数超限则返回 True（防爆破）"""
    now = time.time()
    recent = [t for t in _login_attempts.get(client_ip, []) if now - t < LOGIN_WINDOW_SECONDS]
    if len(recent) >= LOGIN_MAX_ATTEMPTS:
        _login_attempts[client_ip] = recent
        return True
    recent.append(now)
    _login_attempts[client_ip] = recent
    return False


def reset_login_attempts(client_ip: str):
    """登录成功后清空该 IP 的失败计数"""
    _login_attempts.pop(client_ip, None)


@router.get("/api/stats")
async def admin_stats(request: Request):
    """后台仪表盘统计：总留言数 / 今日留言数 / 已审核数"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return JSONResponse(status_code=401, content={"success": False, "error": "未登录或登录过期"})

    mm = get_message_manager()
    if mm is None:
        return {"success": False, "error": "消息管理器未初始化"}

    messages = mm.get_all_messages() or []
    today = datetime.now().strftime('%Y-%m-%d')
    return {
        "success": True,
        "total_messages": len(messages),
        "today_messages": sum(1 for m in messages if str(m.get('timestamp', '')).startswith(today)),
        "approved_messages": len(get_approved_ids())
    }


@router.post("/login")
async def admin_login(request: Request):
    """管理员登录处理（带失败频率限制）"""
    client_ip = request.client.host if request.client else 'unknown'
    if is_login_rate_limited(client_ip):
        return JSONResponse(
            status_code=429,
            content={"success": False, "error": f"尝试过于频繁，请 {LOGIN_WINDOW_SECONDS} 秒后再试"}
        )

    form = await request.form()
    admin_user = form.get('username', '')
    admin_password = form.get('password', '')
    
    if verify_admin(admin_user, admin_password):
        reset_login_attempts(client_ip)
        print(f"管理员 {admin_user} 登录成功")
        response = JSONResponse(content={"success": True})
        response.set_cookie('admin_user', admin_user, max_age=60*60*24*7)
        response.set_cookie('admin_password', admin_password, max_age=60*60*24*7)
        return response
    else:
        return JSONResponse(content={"success": False, "error": "用户名或密码错误"})


@router.get("/logout")
async def admin_logout():
    """管理员登出"""
    response = RedirectResponse(url='/admin/login', status_code=302)
    response.delete_cookie('admin_user')
    response.delete_cookie('admin_password')
    return response


@router.get("/log")
async def admin_log(request: Request, search: str = ""):
    """查看日志"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return RedirectResponse(url='/admin/login', status_code=302)
    
    log_path = 'error.log'
    if not os.path.exists(log_path):
        return {"log_content": []}
    
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.readlines()
    
    if len(content) > 1000:
        content = content[-1000:]
    if search:
        content = [line for line in content if search.lower() in line.lower()]
    
    return {"log_content": content, "search_query": search}


@router.get("/admin_log")
async def admin_admin_log(request: Request, search: str = ""):
    """查看管理员日志"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return RedirectResponse(url='/admin/login', status_code=302)
    
    if not os.path.exists('admin_log.json'):
        return {"log_content": []}
    
    with open('admin_log.json', 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    if len(content) > 1000:
        content = content[-1000:]
    if search:
        content = [line for line in content if search.lower() in line.lower()]
    
    return {"log_content": content, "search_query": search}


@router.post("/delete_message/{message_id}")
async def delete_message(message_id: int, request: Request):
    """删除消息"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return {"success": False, "error": "请先登录"}
    
    permissions = get_admin_user_permissions(admin_user)

    if not check_permission(permissions, "manage_wall_message"):
        return {"success": False, "error": "无权限"}

    mm = get_message_manager()
    if mm is None:
        return {"success": False, "error": "消息管理器未初始化"}
    
    try:
        result = mm.delete_message(message_id)
        
        if result['success']:
            log_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}    {admin_user}删除了深高园校园墙的消息 {message_id}"
            log_admin_data(log_msg)
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/api/delete_comment/{message_id}/{comment_id}")
async def delete_comment(message_id: int, comment_id: str, request: Request):
    """删除评论"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return {"success": False, "error": "请先登录"}
    
    permissions = get_admin_user_permissions(admin_user)
    
    if not check_permission(permissions, "manage_wall_message"):
        return {"success": False, "error": "无权限"}
    
    mm = get_message_manager()
    if mm is None:
        return {"success": False, "error": "消息管理器未初始化"}
    
    try:
        result = mm.delete_comment(message_id, comment_id)
        if result['success']:
            log_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}    {admin_user}删除了消息 {message_id} 的评论 {comment_id}"
            log_admin_data(log_msg)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/messages")
async def admin_get_messages(

    request: Request,
    q: str = "",
    page: int = 1,
    show_all: bool = False
):
    """获取管理消息列表"""
    mm = get_message_manager()
    if mm is None:
        return {"messages": [], "total_pages": 0}
    
    page_size = 20
    
    likes_cookie = request.cookies.get('likes', '')
    likes_list = [int(x) for x in likes_cookie.split(',') if x.isdigit()] if likes_cookie else []
    dislikes_cookie = request.cookies.get('dislikes', '')
    dislikes_list = [int(x) for x in dislikes_cookie.split(',') if x.isdigit()] if dislikes_cookie else []
    
    messages = mm.get_messages(like_list=likes_list, dislike_list=dislikes_list, word=q, filter_type='all')
    
    approved_ids = get_approved_ids()
    
    if not show_all:
        messages = [msg for msg in messages if int(msg['id']) not in approved_ids]
    
    total_pages = (len(messages) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    paginated_messages = messages[start:end]
    
    return {
        "messages": paginated_messages,
        "total_pages": total_pages
    }


@router.get("/api/get_message/{message_id}")
async def admin_get_message(message_id: int, request: Request):
    """获取单条消息"""
    mm = get_message_manager()
    if mm is None:
        return None
    
    likes_cookie = request.cookies.get('likes', '')
    likes_list = [int(x) for x in likes_cookie.split(',') if x.isdigit()] if likes_cookie else []
    dislikes_cookie = request.cookies.get('dislikes', '')
    dislikes_list = [int(x) for x in dislikes_cookie.split(',') if x.isdigit()] if dislikes_cookie else []
    
    return mm.get_message(message_id, like_list=likes_list, dislike_list=dislikes_list)


@router.get("/api/approved_ids")
async def api_get_approved_ids():
    """获取已审核ID列表"""
    approved_ids = get_approved_ids()
    return approved_ids


@router.post("/approve_message/{message_id}")
async def approve_message(message_id: int, request: Request):
    """审核通过消息"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return {"success": False, "error": "请先登录"}
    
    permissions = get_admin_user_permissions(admin_user)
    
    if not check_permission(permissions, "manage_wall_message"):
        return {"success": False, "error": "无权限"}
    
    
    try:
        if not os.path.exists('manage_message.json'):
            manage_data = {"approved": {}}
        else:
            with open('manage_message.json', 'r', encoding='utf-8') as f:
                manage_data = json.load(f)
        
        if 'approved' not in manage_data:
            manage_data['approved'] = {}
        

        
        approved_ids = get_approved_ids()
        if int(message_id) in approved_ids:
            approved_ids.remove(int(message_id))
            return {"success": True, "action": "消息已取消审核"}
        
        manage_data['approved']['lg'].append({
            "id": int(message_id),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "by": admin_user
        })
        
        with open('manage_message.json', 'w', encoding='utf-8') as f:
            json.dump(manage_data, f, ensure_ascii=False, indent=2)
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/repair_message/{message_id}")
async def repair_messages(message_id: int, request: Request):
    """修复消息"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return {"success": False, "error": "请先登录"}
    
    mm = get_message_manager()
    if mm is None:
        return {"success": False, "error": "消息管理器未初始化"}
    
    message = mm.get_message(message_id)
    errors = []
    
    if not message:
        return {"success": False, "error": "消息不存在"}
    
    # 检查并修复文件
    for file in message.get('files', []):
        file_path = os.path.join(settings.UPLOAD_FOLDER, file)
        if not os.path.exists(file_path):
            errors.append(f"文件 {file} 不存在")
            continue
        if is_image_file(file) and get_file_extension(file) != '.png':
            # 转换图片格式
            pass
        elif is_video_file(file) and get_file_extension(file) != '.mp4':
            # 转换视频格式
            pass
    
    # 异步生成缩略图
    if message.get('files'):
        executor.submit(making_tiny_files, message['files'])
    
    log_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}    {admin_user}修复了消息 {message_id}"
    log_admin_data(log_msg)
    
    return {"success": True, "errors": errors}


@router.get("/notice")
async def notice_get(request: Request):
    """公告管理页面"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return RedirectResponse(url='/admin/login', status_code=302)
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>发布公告</title></head>
    <body>
        <h1>发布公告</h1>
        <form method="post" action="/admin/notice">
            <textarea name="text" rows="10" cols="50"></textarea><br>
            <button type="submit">发布</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/notice")
async def notice_post(request: Request):
    """发布公告"""
    admin_user, admin_password = get_admin_session(request)
    if not verify_admin(admin_user, admin_password):
        return RedirectResponse(url='/admin/login', status_code=302)
    
    form = await request.form()
    notice_content = form.get('text', '')
    
    if notice_content:
        # 加载现有公告
        notice_path = os.path.join('static', 'notice.json')
        if os.path.exists(notice_path):
            with open(notice_path, 'r', encoding='utf-8') as f:
                notices = json.load(f)
        else:
            notices = []
        
        notices.append({
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user": f'管理员{admin_user}',
            "content": notice_content
        })
        
        with open(notice_path, 'w', encoding='utf-8') as f:
            json.dump(notices, f, ensure_ascii=False, indent=4)
    
    return RedirectResponse(url='/admin', status_code=302)
