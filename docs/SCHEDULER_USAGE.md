# IKuYo 定时任务调度器使用说明

## 概述

IKuYo 定时任务调度器基于 APScheduler 实现，支持自动定时执行 Mikan Project 动画资源爬虫任务。

## 功能特性

- ✅ 支持 cron 表达式配置
- ✅ 时区设置（默认 Asia/Shanghai）
- ✅ 任务状态监控
- ✅ 错误处理和日志记录
- ✅ 优雅启动和停止

## 快速开始

### 1. 查看任务状态

```bash
python manage_scheduler.py status
```

输出示例：
```
📋 定时任务状态:
   启用状态: ✅ 已启用
   时区设置: Asia/Shanghai

📅 任务配置:
   Mikan爬虫定时任务 (mikan_crawler)
     状态: ✅ 启用
     调度: 0 2 * * *
     描述: 定时爬取Mikan Project动画资源
```

### 2. 测试爬虫任务

```bash
python manage_scheduler.py test
```

### 3. 启动定时调度器

```bash
python manage_scheduler.py start
```

启动后调度器会在后台运行，按 Ctrl+C 停止。

## 配置说明

### 配置文件位置

定时任务配置在 `config.py` 的 `SCHEDULER_CONFIG` 中：

```python
SCHEDULER_CONFIG = {
    "enabled": True,                    # 是否启用定时任务
    "default_cron": "0 2 * * *",       # 默认调度时间
    "timezone": "Asia/Shanghai",       # 时区设置
    "jobs": [
        {
            "id": "mikan_crawler",
            "name": "Mikan爬虫定时任务",
            "cron": "0 2 * * *",       # 每天凌晨2点
            "enabled": True,
            "description": "定时爬取Mikan Project动画资源"
        }
    ]
}
```

### Cron 表达式格式

格式：`分 时 日 月 周`

常用示例：
- `0 2 * * *` - 每天凌晨2点
- `0 */6 * * *` - 每6小时执行一次
- `0 2 * * 1` - 每周一凌晨2点
- `0 2 1 * *` - 每月1号凌晨2点

### 时区设置

支持所有 pytz 时区，常用时区：
- `Asia/Shanghai` - 中国标准时间
- `UTC` - 协调世界时
- `America/New_York` - 美国东部时间

## 日志文件

调度器运行时会生成以下日志文件：
- `scheduler.log` - 调度器运行日志

## 高级配置

### 调度器设置

```python
"scheduler_settings": {
    "job_defaults": {
        "coalesce": False,           # 是否合并错过的任务
        "max_instances": 1,          # 最大实例数
        "misfire_grace_time": 300    # 容错时间（秒）
    }
}
```

### 添加多个任务

```python
"jobs": [
    {
        "id": "mikan_crawler",
        "name": "Mikan爬虫定时任务",
        "cron": "0 2 * * *",
        "enabled": True,
        "description": "定时爬取Mikan Project动画资源"
    },
    {
        "id": "backup_task",
        "name": "数据备份任务",
        "cron": "0 3 * * *",
        "enabled": True,
        "description": "每日数据备份"
    }
]
```

## 故障排除

### 常见问题

1. **任务未执行**
   - 检查 `enabled` 是否为 `True`
   - 验证 cron 表达式格式
   - 查看日志文件

2. **时区问题**
   - 确认时区设置正确
   - 检查系统时区

3. **权限问题**
   - 确保有写入日志文件的权限
   - 检查数据库访问权限

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 生产环境部署

### 1. 使用 systemd 服务

创建服务文件 `/etc/systemd/system/ikuyo-scheduler.service`：

```ini
[Unit]
Description=IKuYo Scheduler
After=network.target

[Service]
Type=simple
User=ikuyo
WorkingDirectory=/path/to/ikuyo
ExecStart=/path/to/uv run python manage_scheduler.py start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable ikuyo-scheduler
sudo systemctl start ikuyo-scheduler
```

### 2. 使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

CMD ["python", "manage_scheduler.py", "start"]
```

### 3. 使用 Supervisor

```ini
[program:ikuyo-scheduler]
command=/path/to/uv run python manage_scheduler.py start
directory=/path/to/ikuyo
user=ikuyo
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ikuyo-scheduler.log
```

## 监控和维护

### 健康检查

定期检查调度器状态：
```bash
python manage_scheduler.py status
```

### 日志监控

监控关键日志：
- 任务执行成功/失败
- 调度器启动/停止
- 错误信息

### 性能优化

- 调整 `misfire_grace_time` 参数
- 监控内存使用情况
- 定期清理日志文件

## 联系支持

如有问题，请查看：
1. 日志文件
2. 配置文件
3. 系统资源使用情况 