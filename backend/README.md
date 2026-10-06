# 深高园校园墙 · FastAPI 后端

配套前端见仓库根目录的 [`frontend/`](../frontend/)（Vue 3 + Vite）。后端只提供 HTTP 接口，与前端源码完全解耦。

## 技术栈

- FastAPI + Uvicorn
- SQLite（留言存储，`static/messages/messages.db`）
- Pillow（图片处理、缩略图）
- FFmpeg（可选，视频转码与缩略图）

## 功能

- 留言：发布、评论、点赞 / 点踩、分区与标签、搜索与热门
- 文件上传：分片上传、合并、直传；图片转 PNG 并生成缩略图到 `static/tiny_files/`
- 公告：读取 / 发布
- 管理员后台：登录校验、留言审核与删除、评论删除、公告管理、操作日志、错误日志
- 邮件发送能力（`mail.py`，当前未接任何路由）

## 安装与运行

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # 按需修改
python app.py               # 默认 0.0.0.0:5412
# 或： uvicorn app:app --host 0.0.0.0 --port 5412 --reload
```

启动后 `GET /health` 返回 `{"status":"ok"}`，接口文档在 `/docs`。

## 配置（`.env`）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `DEBUG` | `False` | 为 `True` 时 `app.py` 会以 reload 模式启动 |
| `SECRET_KEY` | 占位值 | 会话密钥，生产环境必须更换 |
| `HOST` / `PORT` | `0.0.0.0` / `5412` | 监听地址与端口 |
| `SMTP_SERVER` / `SMTP_PORT` | `smtp.126.com` / `465` | 发件服务器 |
| `SENDER_EMAIL` | — | 发件邮箱 |
| `EMAIL_SENDER_PASSWORD` | — | **邮箱客户端授权码**（不是登录密码） |
| `DB_HOST` / `DB_PASSWORD` | 空 | MongoDB，可选 |

CORS 白名单在 [`config.py`](config.py) 的 `ALLOWED_ORIGINS`：前端部署到新域名时，要么把域名加进去，要么用反向代理让请求变成同源。

## 目录说明

```
backend/
├── app.py            # 入口：lifespan、/health、上传相关路由、静态目录挂载
├── config.py         # 配置（pydantic-settings，读取 .env）
├── deps.py           # 全局依赖（消息管理器、公告加载器）
├── msg.py            # 留言管理器（SQLite 读写）
├── tools.py          # 文件校验、图片/视频转换、缩略图、JSON 加载
├── mail.py           # 邮件发送封装
├── database.py       # MongoDB 连接（可选，当前未启用）
├── routes/
│   ├── api.py        # 前缀 /api        列表、详情、公告、标签、分区、热门
│   ├── messages.py   # 前缀 /api/wall   提交、评论、点赞、点踩
│   ├── users.py      # 前缀 /user       登录、头像、资料更新
│   └── admin.py      # 前缀 /api/admin  登录、审核、删除、公告、日志
├── static/           # 运行时数据（见下）
└── logs/info.log     # 运行日志
```

## 运行时数据（不入库）

| 路径 | 内容 |
| --- | --- |
| `static/messages/messages.db` | 留言库 |
| `static/uploads/` | 上传的原文件 |
| `static/tiny_files/` | 缩略图（列表页加载这个目录） |
| `static/notice.json` | 当前公告 |
| `admin_log.json`、`manage_message.json` | 操作日志、待审核记录 |
| `logs/info.log` | 运行日志 |

这些路径已通过 `.git/info/exclude` 忽略，**不会随仓库分发**：部署到新环境时请单独准备或挂载。

## 与 Flask 版本的差异

1. FastAPI 替代 Flask，Pydantic 做数据校验
2. `lifespan` 管理启动/关闭，路由按模块拆分（`routes/`）
3. 默认端口 5412（Flask 版为 5411）
