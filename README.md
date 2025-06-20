# IKuYo 动漫资源爬虫

## 项目简介
IKuYo 是一个面向追番爱好者的动漫资源爬虫，自动化采集 Mikan Project 等站点的番剧资源信息，帮助用户高效追番、聚合分散的更新数据。

## 快速开始

### 环境要求
- Python 3.12 及以上
- 推荐使用 [uv](https://github.com/astral-sh/uv) 管理依赖
- 依赖管理基于 `pyproject.toml`，无需 requirements.txt

### 安装依赖
在项目根目录下执行：
```bash
uv sync
```
此命令会自动根据 pyproject.toml 安装所有依赖。

### 运行示例
- 默认首页模式：
  ```bash
  python scripts/run_crawler.py
  ```
- 按年模式：
  ```bash
  python scripts/run_crawler.py --mode year --year 2024
  ```
- 按季模式：
  ```bash
  python scripts/run_crawler.py --mode season --year 2024 --season 春
  ```
- 全量模式：
  ```bash
  python scripts/run_crawler.py --mode full
  ```
- 增量模式：
  ```bash
  python scripts/run_crawler.py --mode incremental
  ```

## 配置说明
所有参数集中在 `config.yaml`，常用字段如下：
- `database.path`：数据库文件路径
- `site.base_url`：目标站点基础地址
- `crawler.download_delay`：爬取延迟（秒）
- `crawler.concurrent_requests`：并发请求数
- `scheduler.enabled`：是否启用定时任务
- `scheduler.jobs`：定时任务列表（支持 cron 表达式）
- `output.output_dir`：输出目录

如需自定义爬取模式、定时任务、输出路径等，直接修改 `config.yaml` 对应字段。

## 主要功能与用法
- 支持多种爬虫模式：
  - 首页模式：采集首页推荐番剧
  - 按年模式：采集指定年份所有番剧
  - 按季模式：采集指定年份某季度番剧
  - 全量模式：采集所有年份全部番剧
  - 增量模式：仅采集新增/更新番剧
- 定时任务调度：
  - 启动定时任务：`python scripts/manage_scheduler.py start`
  - 查看任务状态：`python scripts/manage_scheduler.py status`
  - 测试任务执行：`python scripts/manage_scheduler.py test`
- 数据输出：所有采集数据和日志均保存在 `data/` 目录下

## 目录结构
```text
IKuYo/
├── config.yaml           # 主配置文件
├── pyproject.toml        # 依赖管理
├── scripts/              # 启动与管理脚本
│   ├── run_crawler.py
│   └── manage_scheduler.py
├── src/                  # 核心代码
│   ├── core/             # 调度与运行核心
│   ├── crawler/          # 爬虫实现与数据结构
│   └── utils/            # 工具模块
├── data/                 # 数据存储
│   ├── database/
│   ├── logs/
│   └── output/
└── docs/                 # 用法文档
```

## 常见问题
- 依赖安装失败：请确认 Python 版本 >=3.12，且已正确安装 uv。
- 网络连接超时：请确认本地网络可访问目标站点。
- 其他问题请查阅 docs/ 目录下的文档。

## 联系方式
- 欢迎通过 GitHub Issues 反馈问题或建议。