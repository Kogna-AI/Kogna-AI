# Kogna-AI 本地安装与运行指南

本文档说明如何在本地安装依赖、配置环境并启动前后端，用于本地调试与前端重设计。

---

## 一、环境要求

在开始前请确保已安装：

| 工具 | 版本要求 | 检查命令 |
|------|----------|----------|
| **Python** | 3.8+ | `python3 --version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 随 Node 安装 | `npm --version` |

---

## 二、后端（Backend）安装与运行

### 1. 进入后端目录

```bash
cd Backend
```

### 2. 创建并激活虚拟环境（推荐）

**macOS / Linux：**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows：**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

在 `Backend` 目录下**新建 `.env` 文件**（可先复制示例再改）：

```bash
# 从示例复制（如有）
cp .env.example .env
# 然后编辑 .env，填入真实配置
```

**.env 最少需要配置：**

- `SECRET_KEY` — **必填**，用于 JWT/会话加密，可先用一组长随机字符串。
- `SUPABASE_URL` — Supabase 项目 URL（登录/数据库会用到）。
- `SUPABASE_KEY` — Supabase Service Role Key（后端用）。
- `DATABASE_URL` — PostgreSQL 连接串（若使用 Supabase，可在 Supabase 控制台拿到）。

**可选（按功能需要再配）：**

- `JWT_SECRET_KEY`、`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`GOOGLE_API_KEY`、`SERPAPI_API_KEY` 等。

### 5. 启动后端服务

在 **Backend** 目录下、虚拟环境已激活时执行：

```bash
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

- 后端地址：**http://localhost:8000**
- API 文档：**http://localhost:8000/api/docs**（Swagger UI）

---

## 三、前端（Frontend）安装与运行

### 1. 进入前端目录

（在项目根目录下执行：）

```bash
cd frontend
```

### 2. 安装依赖

```bash
npm install
```

### 3. 配置环境变量

在 `frontend` 目录下**新建 `.env.local` 文件**（可先复制示例再改）：

```bash
cp .env.example .env.local
# 然后编辑 .env.local
```

**.env.local 需要配置：**

- `NEXT_PUBLIC_SUPABASE_URL` — 与后端使用的 Supabase URL 一致。
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase 的 anon/public key。
- `NEXT_PUBLIC_API_URL` — 本地调试填：**http://localhost:8000**。

### 4. 启动前端开发服务器

在 **frontend** 目录下执行：

```bash
npm run dev
```

- 前端地址：**http://localhost:3000**

---

## 四、同时运行前后端（本地联调）

需要**两个终端**，一个跑后端，一个跑前端。

**终端 1 — 后端：**

```bash
cd Backend
source venv/bin/activate   # Windows: venv\Scripts\activate
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**终端 2 — 前端：**

```bash
cd frontend
npm run dev
```

然后在浏览器打开 **http://localhost:3000** 即可使用前端，前端会请求 **http://localhost:8000** 的 API。

---

## 五、常用开发命令

| 用途 | 命令 |
|------|------|
| 后端热重载 | `cd Backend && python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000` |
| 前端开发 | `cd frontend && npm run dev` |
| 前端构建 | `cd frontend && npm run build` |
| 前端格式化 | `cd frontend && npm run format` |
| 后端测试 | `cd Backend && pytest` |

---

## 六、常见问题

1. **后端启动报错 `SECRET_KEY is not found`**  
   在 `Backend/.env` 中设置 `SECRET_KEY=你的随机密钥`。

2. **前端报错 Supabase 相关**  
   检查 `frontend/.env.local` 中 `NEXT_PUBLIC_SUPABASE_URL` 和 `NEXT_PUBLIC_SUPABASE_ANON_KEY` 是否正确，且无多余空格。

3. **端口被占用**  
   后端默认 8000，前端默认 3000。若被占用可改端口，例如：  
   - 后端：`uvicorn api:app --reload --port 8001`  
   - 前端：`npm run dev -- -p 3001`  
   改前端端口后，需把 `NEXT_PUBLIC_API_URL` 改为对应后端地址（若不同端口也要改后端 CORS 或 `ALLOWED_ORIGINS`）。

4. **Supabase / API Key**  
   若暂时没有 Supabase 或各类 API Key，可先只配 `SECRET_KEY` 和占位 URL/Key 把后端、前端跑起来，登录等依赖 Supabase 的功能会不可用，但页面和本地路由可以用于 UI 调试。

---

## 七、作为 UI/UX 设计师

- 前端代码在 **`frontend/src/`**，页面与路由在 **`frontend/src/app/`**，组件在 **`frontend/src/app/components/`**。
- 修改保存后，前端会热更新；若只改 UI，通常只需跑前端（`npm run dev`），必要时再一起开后端做登录或数据联调。
