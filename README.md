# 深高园校园墙

校园留言墙项目，按技术栈分为两个互不干扰的部分：

| 目录 | 技术栈 | 职责 |
| --- | --- | --- |
| [`frontend/`](frontend/) | **Vue 3 + Vite 7** | 网页前端：页面、组件、路由、样式、接口调用 |
| [`backend/`](backend/) | **FastAPI + Uvicorn** | 后端 API：留言、评论、点赞、文件上传、公告、后台管理 |
| [`pymongodb/`](pymongodb/) | Flask + MongoDB | 可选的用户/数据 API 服务，独立 git 子模块，**当前未接入**主流程 |

两侧只通过 HTTP 接口耦合：前端所有请求都走 `/api/**`、`/static/**`、`/health`，开发环境由 Vite 代理转发到后端，互不依赖对方的源码。

## 目录结构

```
campusWall/
├── frontend/                     # ← Vue 3 前端
│   ├── src/
│   │   ├── components/           # 组件（Layout、MessageCard、PollCard、Modal…）
│   │   ├── views/                # 页面（Home、Wall、Vote、UserProfile、Admin*…）
│   │   ├── services/             # 接口层（api.js、polls.js）
│   │   ├── utils/                # 工具函数
│   │   ├── assets/  App.vue  main.js  style.css
│   ├── public/                   # 静态资源（favicon、_redirects 等原样拷贝到 dist）
│   ├── index.html  vite.config.js  package.json
│   ├── .env  .env.development  .env.production
│   └── dist/                     # 构建产物（不入库）
│
├── backend/                      # ← FastAPI 后端
│   ├── app.py                    # 应用入口（lifespan、上传接口、/health）
│   ├── config.py  deps.py  database.py  mail.py  msg.py  tools.py
│   ├── routes/                   # api.py / messages.py / users.py / admin.py
│   ├── static/                   # 运行时数据（见下方「数据」一节）
│   ├── logs/  .venv/             # 运行日志、虚拟环境（都不入库）
│   ├── requirements.txt  .env  .env.example
│
├── pymongodb/                    # git 子模块（独立仓库）
├── netlify.toml                  # 前端部署配置（必须放在根目录）
└── README.md
```

## 功能特性

- 留言发布、评论、点赞 / 点踩，支持匿名
- 文件上传（图片、视频、文档等，分片上传 + 直传，图片自动生成缩略图）
- 分区与标签、搜索与筛选、热门留言
- **投票**：红（赞成）/ 蓝（反对）双段进度条，每台设备限投一次；发起投票为纯文本
- 管理员后台：留言审核与删除、公告管理、操作日志、错误日志
- 浅色 / 深色主题切换，移动端响应式

## 快速开始

### 环境要求

| | 版本 |
| --- | --- |
| Node.js | **^20.19 或 ≥ 22.12**（Vite 7 的硬性要求） |
| Python | 3.11+ |
| FFmpeg | 可选，用于视频缩略图 |

### 后端（FastAPI，端口 5412）

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 按需填写
python app.py               # 或 uvicorn app:app --host 0.0.0.0 --port 5412 --reload
```

启动后访问 <http://127.0.0.1:5412/health> 应返回 `{"status":"ok"}`。

### 前端（Vue 3，开发端口 5173）

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Vite 已把 `/api`、`/static`、`/health` 代理到 `http://localhost:5412`（见 [`vite.config.js`](frontend/vite.config.js)），所以本地开发时**两个都要启动**，前端不需要配置跨域。

其他命令：`npm run build`（产物到 `frontend/dist`）、`npm run preview`（本地预览构建结果）。

## 环境变量

### 前端 `frontend/`

| 文件 | 作用 |
| --- | --- |
| [`.env`](frontend/.env) | 通用默认值 |
| [`.env.development`](frontend/.env.development) | `npm run dev` 使用：`VITE_API_BASE_URL=http://localhost:5412/` |
| [`.env.production`](frontend/.env.production) | `npm run build` 使用：`VITE_API_BASE_URL` 留空，请求走同源路径（部署时由反向代理转发） |

`VITE_STATIC_URL` 控制静态资源前缀，留空时代码回退为 `/static/`。

### 后端 `backend/`

| 变量 | 说明 |
| --- | --- |
| `DEBUG` | 是否热重载，默认 `False` |
| `SECRET_KEY` | 会话密钥，生产环境务必更换 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | 后台登录账号，**密码只放在 `.env` 里**（`managers.json` 已不再存密码） |
| `HOST` / `PORT` | 监听地址与端口，默认 `0.0.0.0:5412` |
| `SMTP_SERVER` / `SMTP_PORT` / `SENDER_EMAIL` / `EMAIL_SENDER_PASSWORD` | 邮件发送（当前配置为 126 邮箱 `smtp.126.com:465`，密码需填**客户端授权码**而非登录密码） |
| `DB_HOST` / `DB_PASSWORD` | MongoDB，可选 |

CORS 白名单在 [`backend/config.py`](backend/config.py) 的 `ALLOWED_ORIGINS`，部署前端到新域名时需把该域名加进去（或使用反向代理避免跨域）。

## 数据与运行时文件

以下文件由程序运行时读写，**不纳入版本库**（`.git/info/exclude` 已忽略）：

| 路径 | 内容 |
| --- | --- |
| `backend/static/messages/messages.db` | 留言库（SQLite） |
| `backend/static/uploads/` | 上传的原文件 |
| `backend/static/tiny_files/` | 图片/视频缩略图（列表页加载的就是它） |
| `backend/static/notice.json` | 当前生效的公告 |
| `backend/admin_log.json`、`manage_message.json` | 管理员操作日志、待审核记录 |
| `backend/polls.json` | 投票数据（标题、票数、投过票的设备标识） |
| `backend/logs/info.log` | 运行日志 |
| `backend/.env`、`frontend/node_modules/`、`frontend/dist/`、`backend/.venv/` | 配置与依赖产物 |

> 因此用 Docker 部署时镜像里**不含留言数据**，需要挂载数据卷或单独备份 `messages.db` 与 `static/`。

## 主要接口

| 前缀 | 来源 | 示例 |
| --- | --- | --- |
| `/api` | [`routes/api.py`](backend/routes/api.py) | `GET /api/get_messages`、`POST /api/notice`、`POST /api/get_hot_messages`、`POST /api/get_tags`、`POST /api/get_partition_messages`、`POST /api/get_message_details/{id}` |
| `/api/wall` | [`routes/messages.py`](backend/routes/messages.py) | `POST /api/wall/submit`、`POST /api/wall/comment/{id}`、`POST /api/wall/like/{id}`、`POST /api/wall/dislike/{id}` |
| `/api/admin` | [`routes/admin.py`](backend/routes/admin.py) | `POST /api/admin/login`、`GET /api/admin/verify`、`GET /api/admin/api/messages`、`POST /api/admin/delete_message/{id}`、`GET/POST /api/admin/notice`、`GET /api/admin/log` |
| `/user` | [`routes/users.py`](backend/routes/users.py) | `GET /user/{id}/avatar`、`POST /user/login` |
| 其他 | [`app.py`](backend/app.py) | `GET /health`、`POST /api/chunked_upload`、`POST /api/merge_chunks`、`POST /api/direct_upload` |
| 静态 | `app.mount("/static")` | `/static/uploads/<file>`、`/static/tiny_files/<file>` |
| `/api/polls` | [`routes/polls.py`](backend/routes/polls.py) | `GET /api/polls?voter_id=`（列表，含本设备投票状态）、`POST /api/polls`（发起）、`POST /api/polls/{id}/vote`（投票）；数据存 `backend/polls.json`，按设备 `voter_id` 去重 |

## 部署

### 前端 → Netlify

仓库根目录的 [`netlify.toml`](netlify.toml) 已配好：

- **构建**：`base = frontend`、`command = npm run build`、`publish = dist`、`NODE_VERSION = 22`
- **反向代理**：`/api/*`、`/static/*` 转发到线上后端，浏览器只发同源请求，从而**不受后端 CORS 白名单限制**
- **SPA 回退**：`/*  →  /index.html  200`，保证 `/vote` 等路由直接访问或刷新不 404

> 注意 `netlify.toml` 的优先级高于 Netlify 网页端的 Build settings，改配置文件即可生效。

### 生产环境现状（2026-10 上线，维护时看这一节）

| 部分 | 位置 / 配置 |
| --- | --- |
| 前端 | Netlify 站点 `https://tranquil-beijinho-43aae8.netlify.app`，从本仓库 `main` 分支自动构建（配置见根目录 [`netlify.toml`](netlify.toml)：`base=frontend`、`npm run build`、`publish=dist`、`NODE_VERSION=22`） |
| 后端 | 腾讯云服务器 `193.112.17.150`；代码 `/www/wwwroot/default/backend/backend`，虚拟环境 `/www/wwwroot/default/backend/venv` |
| 进程 | systemd 服务 **`campuswall`**：`venv/bin/uvicorn app:app --host 0.0.0.0 --port 5412`，`User=www`、`Restart=always`，已开机自启 |
| 端口放行 | ① 腾讯云控制台**安全组**：放行 `TCP:5412`（来源 `0.0.0.0/0`）② **宝塔面板 → 安全**：放行 `5412/TCP`（宝塔防火墙直接写 iptables 的 `IN_BT` 链，漏了这条外网就是不通） |
| 请求链路 | 浏览器 → Netlify（`/api/*`、`/static/*` 反向代理）→ `http://193.112.17.150:5412`；因此**无需 CORS 白名单、后端也无需 HTTPS 证书** |
| 数据 | 留言库 `backend/static/messages/messages.db`、原图 `static/uploads/`、缩略图 `static/tiny_files/` —— 都在服务器上，**不在仓库里** |
| 日志 | `backend/logs/info.log`（业务日志）、`journalctl -u campuswall`（服务日志） |

服务器上的常用命令：

```bash
systemctl status campuswall --no-pager       # 服务状态
systemctl restart campuswall                 # 改完后端代码后重启
journalctl -u campuswall -n 50 --no-pager    # 启动/报错日志
ss -lntp | grep ':5412'                      # 确认是谁在监听 5412
tail -f /www/wwwroot/default/backend/backend/logs/info.log   # 实时业务日志
```

维护注意：

- **前端生产构建必须走同源**：`frontend/.env.production` 里 `VITE_API_BASE_URL` 保持留空（`api.js` 把「显式留空」视为同源，交由 Netlify 反向代理）。若在构建里写死后端地址，浏览器会绕过代理直接跨域请求而被拒。
- **后端没有 CI**：改完 `backend/` 的代码要手动把对应文件上传到服务器，再 `systemctl restart campuswall`；只改前端则提交推送后 Netlify 会自动重建。
- 同一个 5412 端口只能有一个进程监听：若用 `systemctl` 管理服务，就**不要**再手动前台跑 `uvicorn`，否则 systemd 会因 `address already in use` 无限重启。
- 建议用宝塔「计划任务」每天打包备份 `backend/static/`。

### 后端 → 需要能常驻 Python 的环境

Netlify / Cloudflare Pages 这类静态托管**跑不了 FastAPI**，后端需要 VPS、Docker、Render、Railway 等。切换后端地址时二选一：

1. 改 `netlify.toml` 中两条 `[[redirects]]` 的 `to`（推荐，仍然无跨域问题）；
2. 在 Netlify 环境变量里设 `VITE_API_BASE_URL`（Vite 中真实环境变量优先级高于 `.env`），同时把该域名加入后端 `ALLOWED_ORIGINS`。

### Docker 参考（前后端同镜像）

```dockerfile
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist ./static
EXPOSE 5412
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5412"]
```

> 该镜像只把前端产物放进了后端的 `static/`（即 `/static/index.html`）；若要通过根路径 `/` 访问前端，需再加一条返回 `index.html` 的路由，或用 Nginx 之类的反向代理。

## pymongodb（可选子模块）

独立的 Flask + MongoDB API 服务，与主流程解耦。需要时再拉取与启动：

```bash
git submodule update --init --recursive
cd pymongodb
pip install -r requirements.txt
python run.py
```

详细说明见 <https://github.com/renzhen666666/pymongodb>。
