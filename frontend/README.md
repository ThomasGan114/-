# 深高园校园墙 · Vue 3 前端

配套后端见仓库根目录的 [`backend/`](../backend/)（FastAPI）。前端只通过 HTTP 接口与后端通信，两者可独立开发与部署。

## 技术栈

- Vue 3（`<script setup>` SFC）+ Vue Router 4（history 模式）
- Vite 7 —— **要求 Node.js ^20.19 或 ≥ 22.12**
- Axios（`withCredentials`）、Bootstrap 5 + Bootstrap Icons、dayjs

## 目录结构

```
frontend/
├── src/
│   ├── components/   # Layout（侧边栏 / 顶栏）、MessageCard(Mini)、PollCard、Modal、
│   │                 # UserCard(Simple/Mini)、FilePreviewModal、Footer…
│   ├── views/        # Home、Wall、Vote、Partition、UserProfile、MessageDetail、Admin*…
│   ├── services/     # api.js（axios 实例 + 全部接口）、polls.js（投票数据层）
│   ├── utils/        # userPage.js 等
│   ├── assets/  App.vue  main.js  style.css
├── public/           # favicon.ico / favicon.png / static/（校徽、旧静态资源）
├── index.html  vite.config.js  package.json
├── .env  .env.development  .env.production
└── dist/             # 构建产物（不入库）
```

- 路由表：`src/main.js`
- 侧边栏菜单项与页面标题：`src/components/Layout.vue` 的 `navItems`
- 所有后端请求集中在 `src/services/api.js`（改接口只动这一个文件）

## 开发

```bash
npm install
npm run dev        # http://localhost:5173
```

[`vite.config.js`](vite.config.js) 已把 `/api`、`/static`、`/health` 代理到 `http://localhost:5412`，所以本地开发**需要先启动后端**，前端无需处理跨域。

> Windows 上如遇 dev server 因文件监听 `EBUSY` 崩溃，配置里已启用 `server.watch.usePolling`（轮询监听）。

其他命令：

```bash
npm run build      # 产物输出到 dist/
npm run preview    # 本地预览构建结果
```

## 环境变量

| 文件 | 用途 |
| --- | --- |
| [`.env`](.env) | 通用默认值 |
| [`.env.development`](.env.development) | `npm run dev` 使用：`VITE_API_BASE_URL=http://localhost:5412/` |
| [`.env.production`](.env.production) | `npm run build` 使用：`VITE_API_BASE_URL` 留空 → 请求走同源路径，交给部署层的反向代理 |

`VITE_STATIC_URL` 控制静态资源前缀，留空时代码回退为 `/static/`。Vite 中**真实环境变量优先级高于 `.env`**，因此 Netlify 上可直接用环境变量覆盖。

## 样式约定

- 主题色 `--primary-color: #FF0073`（深色档 `#CC005C`、浅色档 `#FF4D9E`），定义在 [`src/style.css`](src/style.css)
- 深浅色主题通过 `<html data-theme="light|dark">` 切换；组件统一使用 `var(--card-bg)`、`var(--border-color)`、`var(--text-primary)`、`var(--hover-bg)` 等变量，避免写死颜色
- 卡片圆角 12–16px、悬浮阴影与校园墙列表保持一致的观感

## 部署

仓库根目录的 [`netlify.toml`](../netlify.toml) 已配好：`base = frontend`、`command = npm run build`、`publish = dist`、`NODE_VERSION = 22`，并包含 `/api`、`/static` 反向代理与 SPA 回退规则。
