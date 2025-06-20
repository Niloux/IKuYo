# IKuYo - 动画资源爬虫系统

基于 Scrapy 框架的 Mikan Project 动画资源爬虫系统，支持定时任务调度和数据库存储。

## 🚀 功能特性

- ✅ **高效爬虫**：基于 Scrapy 框架，支持并发爬取
- ✅ **数据存储**：SQLite 数据库存储，结构化数据管理
- ✅ **定时任务**：APScheduler 定时调度，自动化运行
- ✅ **配置管理**：灵活的配置文件，支持测试/生产模式
- ✅ **错误处理**：完善的异常处理和重试机制
- ✅ **日志记录**：详细的运行日志和状态监控

## 📁 项目结构

```
IKuYo/
├── src/ikuyo/                 # 源代码目录
│   ├── config.py             # 配置管理
│   ├── core/                 # 核心功能
│   │   └── scheduler.py      # 定时任务调度器
│   ├── crawler/              # 爬虫模块
│   │   ├── items.py          # 数据项定义
│   │   ├── middlewares.py    # 中间件
│   │   ├── pipelines.py      # 数据处理管道
│   │   ├── settings.py       # Scrapy设置
│   │   └── spiders/          # 爬虫定义
│   │       └── mikan.py      # Mikan爬虫
│   └── utils/                # 工具模块
├── scripts/                  # 脚本目录
│   ├── manage_scheduler.py   # 调度器管理
│   └── run_crawler.py        # 爬虫运行
├── docs/                     # 文档目录
├── data/                     # 数据目录
│   ├── database/             # 数据库文件
│   ├── logs/                 # 日志文件
│   └── output/               # 输出文件
└── tests/                    # 测试目录
```

## 🛠️ 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd IKuYo

# 安装依赖
uv sync
```

### 2. 运行爬虫

```bash
# 测试模式（爬取3个动画）
python scripts/run_crawler.py --test --limit 3

# 指定URL爬取
python scripts/run_crawler.py --url "https://mikanani.me/Home/Bangumi/3015"

# 生产模式
python scripts/run_crawler.py
```

### 3. 定时任务

```bash
# 查看任务状态
python scripts/manage_scheduler.py status

# 启动定时调度器
python scripts/manage_scheduler.py start

# 测试任务执行
python scripts/manage_scheduler.py test
```

## ⚙️ 配置说明

### 爬虫配置

在 `src/ikuyo/config.py` 中配置：

```python
CRAWLER_CONFIG = {
    "test_mode": True,        # 测试模式
    "test_limit": 3,          # 测试限制数量
    "download_delay": 1,      # 请求延迟
    "concurrent_requests": 16, # 并发请求数
    "retry_times": 3,         # 重试次数
}
```

### 定时任务配置

```python
SCHEDULER_CONFIG = {
    "enabled": True,          # 启用定时任务
    "timezone": "Asia/Shanghai", # 时区
    "jobs": [
        {
            "id": "mikan_crawler",
            "cron": "0 2 * * *",  # 每天凌晨2点
            "enabled": True,
        }
    ]
}
```

## 📊 数据模型

### 动画信息 (animes)
- `mikan_id`: Mikan ID
- `title`: 动画标题
- `bangumi_id`: Bangumi ID
- `description`: 描述信息

### 字幕组 (subtitle_groups)
- `id`: 字幕组ID
- `name`: 字幕组名称
- `is_subscribed`: 是否订阅

### 资源文件 (resources)
- `mikan_id`: 关联动画ID
- `subtitle_group_id`: 字幕组ID
- `title`: 资源标题
- `magnet_url`: 磁力链接
- `file_size`: 文件大小

## 🔧 开发指南

### 添加新的爬虫

1. 在 `src/ikuyo/crawler/spiders/` 创建新的爬虫文件
2. 继承 `scrapy.Spider` 类
3. 实现 `parse` 方法
4. 在 `settings.py` 中注册

### 扩展数据处理

1. 在 `src/ikuyo/crawler/pipelines.py` 添加新的 Pipeline
2. 实现 `process_item` 方法
3. 在 `settings.py` 中配置 Pipeline 顺序

### 自定义中间件

1. 在 `src/ikuyo/crawler/middlewares.py` 添加中间件
2. 实现相应的方法
3. 在 `settings.py` 中启用

## 📝 日志和监控

### 日志文件位置
- 爬虫日志：`data/logs/crawler.log`
- 调度器日志：`data/logs/scheduler.log`

### 监控指标
- 爬取数量统计
- 错误率监控
- 执行时间统计
- 数据库状态

## 🚀 部署指南

### 生产环境部署

1. **使用 systemd 服务**
```bash
sudo systemctl enable ikuyo-scheduler
sudo systemctl start ikuyo-scheduler
```

2. **使用 Docker**
```bash
docker build -t ikuyo .
docker run -d --name ikuyo-scheduler ikuyo
```

3. **使用 Supervisor**
```bash
supervisorctl start ikuyo-scheduler
```

详细部署说明请参考 `docs/DEPLOYMENT.md`

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目主页：[GitHub Repository]
- 问题反馈：[Issues]
- 功能建议：[Discussions]

---

**IKuYo** - 让动画资源获取更简单 🎬
