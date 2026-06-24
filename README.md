# MyBlog - 个人博客项目

从0到1构建的个人博客系统，基于 FastAPI + React。

## 技术栈

- **后端**: Python FastAPI, SQLAlchemy (async), PostgreSQL, JWT
- **前端**: React 19, Vite, Ant Design, React Router
- **部署**: Docker Compose

## 快速启动

### 1. 启动数据库

```bash
docker compose up -d db
```

### 2. 启动后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 项目结构

```
blog/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── core/      # 配置、安全、数据库
│   │   ├── models/    # SQLAlchemy 模型
│   │   ├── schemas/   # Pydantic 验证
│   │   └── utils/     # 工具函数
│   ├── alembic/       # 数据库迁移
│   └── requirements.txt
├── frontend/          # React 前端
│   └── src/
│       ├── api/       # API 请求层
│       ├── pages/     # 页面组件
│       ├── components/ # 通用组件
│       └── contexts/  # React Context
└── docker-compose.yml # 容器编排
```
