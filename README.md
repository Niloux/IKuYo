<div align="center">

# 🎬 IKuYo 动漫资源爬虫

<img src="assets/ikuyo.png" alt="IKuYo Avatar" width="200" height="200">

*面向追番爱好者的智能动漫资源采集工具*

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-latest-green.svg)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Scrapy](https://img.shields.io/badge/Scrapy-2.13+-red.svg)](https://scrapy.org/)

</div>

---

## 📖 项目简介

IKuYo 是一个面向追番爱好者的动漫资源爬虫，自动化采集 **Mikan Project** 站点的番剧资源信息，帮助用户高效追番、聚合分散的更新数据。

### ✨ 主要特性

- 🚀 **多模式采集**：支持首页、按年、按季、全量、增量等多种采集策略
- ⏰ **定时调度**：内置 APScheduler 定时任务，自动化追番更新
- 🎯 **精准解析**：智能识别番剧信息、字幕组、资源链接等关键数据
- 💾 **本地存储**：SQLite 数据库持久化，支持数据导出和分析
- 🔧 **配置驱动**：YAML 配置文件，灵活自定义采集参数
- 🚀 **RESTful API**：FastAPI驱动的查询接口，支持分页、搜索、过滤

---

## 🚀 快速开始

### 📋 环境要求

- 🐍 **Python 3.12** 及以上版本
- 📦 推荐使用 [**uv**](https://github.com/astral-sh/uv) 管理依赖
- 📄 依赖管理基于 `pyproject.toml`

### 📥 安装依赖

在项目根目录下执行：

```bash
uv sync
```

> 💡 此命令会自动根据 pyproject.toml 安装所有依赖

### 🎮 运行示例

| 模式 | 命令 | 说明 |
|------|------|------|
| 🏠 **首页模式** | `uv run python scripts/run_crawler.py` | 采集首页推荐番剧 |
| 📅 **按年模式** | `uv run python scripts/run_crawler.py --mode year --year 2024` | 采集2024年所有番剧 |
| 🍃 **按季模式** | `uv run python scripts/run_crawler.py --mode season --year 2024 --season 春` | 采集2024年春季番剧 |
| 🌐 **全量模式** | `uv run python scripts/run_crawler.py --mode full` | 采集所有年份番剧 |
| 🔄 **增量模式** | `uv run python scripts/run_crawler.py --mode incremental` | 仅采集新增/更新番剧 |

### 🎮 启动API服务

```bash
# 开发模式（支持热重载）
uv run python scripts/run_api.py --reload --debug

# 生产模式
uv run python scripts/run_api.py --host 0.0.0.0 --port 8000
```

---

## ⚙️ 配置说明

所有参数集中在 `config.yaml`，主要字段说明：

```yaml
database:
  path: data/database/ikuyo.db    # 📁 数据库文件路径

site:
  base_url: https://mikanani.me   # 🌐 目标站点地址
  
crawler:
  download_delay: 0.1             # ⏱️ 爬取延迟（秒）
  concurrent_requests: 32         # 🔄 并发请求数
  
scheduler:
  enabled: true                   # 📅 启用定时任务
  jobs:                          # 📋 任务列表
    - cron: "0 2 * * *"          # 🕐 每天凌晨2点执行
```

---

## 🎯 主要功能

### 🕷️ 爬虫模式

<table>
  <tr>
    <th>模式</th>
    <th>适用场景</th>
    <th>数据量</th>
    <th>推荐频率</th>
  </tr>
  <tr>
    <td>🏠 首页模式</td>
    <td>关注热门新番</td>
    <td>少量</td>
    <td>每日</td>
  </tr>
  <tr>
    <td>📅 按年模式</td>
    <td>补全年度番剧</td>
    <td>中等</td>
    <td>按需</td>
  </tr>
  <tr>
    <td>🍃 按季模式</td>
    <td>季度新番追踪</td>
    <td>中等</td>
    <td>每季</td>
  </tr>
  <tr>
    <td>🌐 全量模式</td>
    <td>构建完整数据库</td>
    <td>大量</td>
    <td>初次/定期</td>
  </tr>
  <tr>
    <td>🔄 增量模式</td>
    <td>日常更新维护</td>
    <td>少量</td>
    <td>每日</td>
  </tr>
</table>

### ⏰ 定时任务管理

```bash
# 📊 查看任务状态
uv run python scripts/manage_scheduler.py status

# 🚀 启动定时调度
uv run python scripts/manage_scheduler.py start

# 🧪 测试任务执行
uv run python scripts/manage_scheduler.py test
```

### 💾 数据输出

所有采集数据和日志均保存在 `data/` 目录下：

- 📁 `data/database/` - SQLite 数据库文件
- 📁 `data/logs/` - 运行日志
- 📁 `data/output/` - 导出数据

---

## 📁 目录结构

```text
IKuYo/
├── 📄 config.yaml              # 主配置文件
├── 📄 pyproject.toml           # 依赖管理
├── 🖼️ assets/                  # 静态资源
│   └── ikuyo.png
├── 📁 scripts/                 # 启动与管理脚本
│   ├── run_crawler.py
│   └── manage_scheduler.py
├── 📁 ikuyo/                   # 主要代码包
│   ├── core/                  # 核心功能模块
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库抽象层
│   │   ├── scheduler.py       # 任务调度器
│   │   └── crawler_runner.py  # 爬虫运行器
│   ├── crawler/               # 爬虫模块（独立）
│   │   ├── spiders/           # 爬虫实现
│   │   ├── items.py           # 数据结构定义
│   │   ├── pipelines.py       # 数据处理管道
│   │   └── settings.py        # 爬虫配置
│   ├── api/                   # RESTful API模块
│   │   ├── main.py           # FastAPI应用入口
│   │   ├── routes/           # API路由
│   │   │   ├── animes.py     # 动画相关API
│   │   │   ├── resources.py  # 资源相关API
│   │   │   └── health.py     # 健康检查API
│   │   └── models/           # 数据模型
│   │   └── schemas.py        # Pydantic模型定义
│   └── utils/                 # 工具模块
│       └── text_parser.py     # 文本解析工具
├── 📁 data/                   # 数据存储
│   ├── database/              # SQLite 数据库
│   ├── logs/                  # 运行日志
│   └── output/                # 导出数据
├── 📁 tests/                  # 测试代码
└── 📁 docs/                   # 用法文档
    ├── CRAWL_MODES_USAGE.md
    └── SCHEDULER_USAGE.md
```

---

## ❓ 常见问题

<details>
<summary>🔧 依赖安装失败</summary>

- 确认 Python 版本 >= 3.12
- 确认已正确安装 uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`
- 尝试清理缓存后重新安装：`uv cache clean && uv sync`

</details>

<details>
<summary>🌐 网络连接超时</summary>

- 确认本地网络可访问目标站点
- 检查代理设置或防火墙配置
- 适当增加 `config.yaml` 中的 `download_delay` 值

</details>

<details>
<summary>📚 更多问题</summary>

请查阅 `docs/` 目录下的详细文档，或通过 GitHub Issues 反馈。

</details>

---

## 🛣️ 开发计划

项目正在持续开发中，后续计划实现以下功能：

### 🎯 高优先级
- ✅ ~~**数据库表结构优化**~~ - 提升查询性能和存储效率
- ✅ ~~**项目架构重构**~~ - 采用模块平行架构，职责分离清晰
- ✅ ~~**数据查询API**~~ - 封装数据库查询功能，提供便捷的数据访问接口
- 📺 **追番功能实现** - 个人追番列表管理，订阅更新提醒
- 🐧 **RSS订阅功能实现** - 通过mikan的rss链接订阅某个番剧或某个番剧+某个字幕组的动画资源
- 🥣 **一个好看实用的界面** - 一个好看实用的界面，可以方便的查看番剧信息、资源信息、追番信息等

### 🎨 中优先级
- ✅ ~~**Bangumi API集成**~~ - 集成Bangumi数据，丰富番剧元信息

### 🚀 低优先级
- ⬇️ **自动下载功能** - 集成aria2等下载器，实现追番资源自动下载
- 🛜 **Bangumi API缓存** - 集成缓存，提升性能

> 💡 开发优先级：架构重构 → 查询API → 追番功能 → Bangumi集成 → 自动下载

### 🏗️ 架构说明

项目采用**模块平行架构**，各模块职责清晰：

- **`ikuyo/core/`** - 核心功能模块：配置管理、数据库抽象层、任务调度等
- **`ikuyo/crawler/`** - 爬虫模块：专注数据采集，包含Scrapy相关组件
- **`ikuyo/api/`** - RESTful API模块：提供查询接口
- **`ikuyo/utils/`** - 工具模块：提供通用的工具函数

此架构设计便于：
- 🔧 **独立开发**：各模块可以独立开发和测试
- 🚀 **功能扩展**：后续API、追番、RSS等功能可作为平行模块添加
- 🏃 **维护升级**：模块间依赖清晰，便于维护和升级

欢迎对功能需求和优先级提出建议！

---

## 🙏 鸣谢

感谢以下开源项目和资源：

### 🛠️ 核心技术栈
- [**Scrapy**](https://scrapy.org/) - 强大的网页爬虫框架
- [**APScheduler**](https://apscheduler.readthedocs.io/) - Python 定时任务调度库
- [**uv**](https://github.com/astral-sh/uv) - 快速的 Python 包管理工具
- [**SQLite**](https://www.sqlite.org/) - 轻量级数据库引擎

### 🎨 资源与灵感
- [**Mikan Project**](https://mikanani.me/) - 提供丰富的动漫资源数据
- **《孤独摇滚》** - 感谢归去来兮女士的命名灵感

### 📦 依赖包
- `beautifulsoup4` - HTML/XML 解析
- `requests` - HTTP 请求处理
- `pyyaml` - YAML 配置文件支持

---

## 📞 联系方式

<div align="center">

🐛 **遇到问题？** 欢迎通过 [GitHub Issues](https://github.com/Niloux/IKuYo/issues) 反馈

💡 **有好想法？** 随时提交 [Pull Request](https://github.com/Niloux/IKuYo/pulls) 

📧 **其他交流** 请在 Issue 区留言，作者会及时回复

---

*Made with ❤️ by [@归去来兮](https://zh.moegirl.org.cn/%E5%96%9C%E5%A4%9A%E9%83%81%E4%BB%A3)*

</div>

---

## 🎯 API使用指南

### 基础信息

- **API地址**：http://localhost:8000
- **API文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/api/v1/health/

### 主要接口

#### 1. 健康检查

```bash
# 基础健康检查
GET /api/v1/health/

# 统计信息
GET /api/v1/health/stats
```

#### 2. 动画相关

```bash
# 获取动画列表（支持分页、搜索）
GET /api/v1/animes/?page=1&per_page=20&q=关键词

# 获取动画详情
GET /api/v1/animes/{mikan_id}

# 获取动画资源
GET /api/v1/animes/{mikan_id}/resources

# 搜索动画
GET /api/v1/animes/search/{keyword}
```

#### 3. 资源相关

```bash
# 获取资源列表（支持过滤）
GET /api/v1/resources/?page=1&per_page=20&anime_id=123&resolution=1080p

# 获取资源详情
GET /api/v1/resources/{resource_id}

# 按动画查询资源
GET /api/v1/resources/anime/{anime_id}

# 按分辨率搜索
GET /api/v1/resources/search/resolution/{resolution}

# 获取最新资源
GET /api/v1/resources/latest/{count}
```

### 响应格式

所有API响应都遵循统一格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

## 📞 联系方式

<div align="center">

🐛 **遇到问题？** 欢迎通过 [GitHub Issues](https://github.com/Niloux/IKuYo/issues) 反馈

💡 **有好想法？** 随时提交 [Pull Request](https://github.com/Niloux/IKuYo/pulls) 

📧 **其他交流** 请在 Issue 区留言，作者会及时回复

---

*Made with ❤️ by [@归去来兮](https://zh.moegirl.org.cn/%E5%96%9C%E5%A4%9A%E9%83%81%E4%BB%A3)*

</div>