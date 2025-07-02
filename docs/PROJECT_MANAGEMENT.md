# IKuYo 项目管理指南

## 📋 Git 仓库结构

### 当前配置
- **主仓库**: `/Users/wuyou/Projects/IKuYo` (包含整个项目)
- **统一管理**: frontend作为主项目的子目录，无独立Git仓库

### 优势
✅ **代码同步**: 前后端代码版本统一管理
✅ **简化部署**: 单一仓库便于CI/CD配置
✅ **历史追踪**: 完整的项目演进历史
✅ **协作友好**: 团队成员只需克隆一个仓库

## 🚀 开发工作流

### 日常开发
```bash
# 1. 启动后端服务
cd /Users/wuyou/Projects/IKuYo
python scripts/run_api.py --host 127.0.0.1 --port 8000 &

# 2. 启动前端开发服务
cd frontend
npm run dev &

# 3. 开发完成后提交
git add .
git commit -m "feat: 描述你的更改"
git push origin master
```

### 分支策略建议
```bash
# 开发新功能
git checkout -b feature/feature-name
# 修复Bug
git checkout -b hotfix/bug-description
# 发布准备
git checkout -b release/v1.0.0
```

## 📦 构建与部署

### 前端构建
```bash
cd frontend
npm run build
# 构建产物在 frontend/dist/
```

### 后端部署
```bash
# 生产环境启动
python scripts/run_api.py --host 0.0.0.0 --port 8000 --reload false --debug false
```

## 🎯 未来架构规划

### Phase 1: Web应用 (当前)
- Vue 3 + FastAPI
- 响应式设计
- RESTful API

### Phase 2: 桌面应用
- Vue 3 + Tauri
- 跨平台桌面端
- 本地数据同步

### Phase 3: 移动应用
- Vue 3 + Capacitor
- iOS/Android APP
- 离线支持

## 📁 重要文件说明

### 配置文件
- `pyproject.toml` - Python项目配置
- `frontend/package.json` - Node.js依赖管理
- `frontend/vite.config.ts` - Vite构建配置
- `config.yaml` - 应用配置文件

### 开发脚本
- `scripts/run_api.py` - API服务启动
- `scripts/run_crawler.py` - 爬虫执行
- `scripts/manage_scheduler.py` - 任务调度管理

### 数据目录
- `data/database/` - SQLite数据库文件
- `data/logs/` - 应用日志
- `data/output/` - 爬虫输出

## 🔧 环境配置

### Python环境
```bash
# 使用uv管理依赖
uv sync
source .venv/bin/activate
```

### Node.js环境
```bash
cd frontend
npm install
```

## 📊 项目统计
- **后端API**: 已完成核心功能
- **前端界面**: 基础功能完成，可继续扩展
- **数据库**: 83个番剧，4417个资源记录
- **爬虫**: 96个字幕组数据源

## 🎯 下一步计划
1. 完善前端UI/UX设计
2. 添加用户偏好设置
3. 实现资源下载功能
4. 优化移动端体验
5. 准备跨平台APP开发
