# Mikan Project 爬虫 - 多种爬取模式使用指南

## 概述

IKuYo 爬虫系统支持多种灵活的爬取模式，可以根据不同的需求选择合适的爬取策略。本指南详细介绍各种模式的使用方法、配置选项和最佳实践。

## 支持的爬取模式

### 1. 首页模式 (homepage) - 默认模式

**用途**: 爬取Mikan Project首页展示的动画，适合日常更新和监控

**特点**:
- 爬取首页当前展示的动画列表
- 数据量相对较小，适合快速更新
- 适合定时任务和日常监控

**使用示例**:
```bash
# 默认首页模式
python scripts/run_crawler.py

# 测试模式，限制爬取数量
python scripts/run_crawler.py --test --limit 5
```

**配置选项**:
```python
# src/config.py
CRAWL_MODE_CONFIG = {
    "mode": "homepage",  # 默认模式
    # 其他配置...
}
```

### 2. 年份模式 (year)

**用途**: 爬取指定年份的所有季度动画

**特点**:
- 爬取指定年份的春、夏、秋、冬四个季度
- 数据量适中，适合按年份整理数据
- 适合历史数据补全

**使用示例**:
```bash
# 爬取2024年所有季度动画
python scripts/run_crawler.py --mode year --year 2024

# 测试模式，限制爬取数量
python scripts/run_crawler.py --mode year --year 2024 --test --limit 10
```

**配置选项**:
```python
# src/config.py
CRAWL_MODE_CONFIG = {
    "mode": "year",
    "year": 2024,  # 指定年份
    # 其他配置...
}
```

### 3. 季度模式 (season)

**用途**: 爬取指定年份和季度的动画

**特点**:
- 精确控制爬取范围
- 数据量可控，适合特定需求
- 适合季度数据分析和整理

**使用示例**:
```bash
# 爬取2024年春季动画
python scripts/run_crawler.py --mode season --year 2024 --season 春

# 爬取2023年夏季动画
python scripts/run_crawler.py --mode season --year 2023 --season 夏
```

**配置选项**:
```python
# src/config.py
CRAWL_MODE_CONFIG = {
    "mode": "season",
    "year": 2024,
    "season": "春",  # 春、夏、秋、冬
    # 其他配置...
}
```

### 4. 全量模式 (full)

**用途**: 爬取2013-2025年所有动画数据

**特点**:
- 数据量最大，包含所有历史数据
- 适合首次部署和完整数据同步
- 需要较长时间和较多资源

**使用示例**:
```bash
# 全量爬取（会提示确认）
python scripts/run_crawler.py --mode full

# 测试模式，只爬取少量数据
python scripts/run_crawler.py --mode full --test --limit 20
```

**配置选项**:
```python
# src/config.py
CRAWL_MODE_CONFIG = {
    "mode": "full",
    "year_range": {"start": 2013, "end": 2025},
    # 其他配置...
}
```

### 5. 增量模式 (incremental)

**用途**: 只爬取新增或更新的动画

**特点**:
- 基于时间戳的增量更新
- 数据量最小，效率最高
- 适合频繁的定时更新

**使用示例**:
```bash
# 增量更新
python scripts/run_crawler.py --mode incremental

# 测试增量更新
python scripts/run_crawler.py --mode incremental --test
```

**配置选项**:
```python
# src/config.py
CRAWL_MODE_CONFIG = {
    "mode": "incremental",
    "incremental": {
        "enabled": True,
        "last_crawl_time": "2024-01-01T00:00:00",
        "check_interval": 3600,  # 1小时
    },
    # 其他配置...
}
```

## 命令行参数详解

### 基本参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--mode` | 字符串 | 爬取模式 | `--mode year` |
| `--year` | 整数 | 爬取年份 | `--year 2024` |
| `--season` | 字符串 | 爬取季度 | `--season 春` |
| `--test` | 标志 | 启用测试模式 | `--test` |
| `--limit` | 整数 | 测试模式限制数量 | `--limit 10` |

### 高级参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--start-url` | 字符串 | 指定起始URL | `--start-url "https://mikanani.me/Home/Bangumi/1234"` |
| `--output` | 字符串 | 输出文件路径 | `--output data/output/anime.json` |
| `--log-level` | 字符串 | 日志级别 | `--log-level DEBUG` |

### 参数验证规则

1. **年份模式**: 必须指定 `--year`，年份范围 2013-2025
2. **季度模式**: 必须指定 `--year` 和 `--season`
3. **测试模式**: `--limit` 必须大于 0
4. **全量模式**: 会提示用户确认，因为数据量很大

## 配置文件详解

### 爬取模式配置

```python
# src/config.py
CRAWL_MODE_CONFIG = {
    # 爬取模式：homepage, year, season, full, incremental
    "mode": "homepage",
    
    # 指定年份（年份模式或季度模式时使用）
    "year": None,
    
    # 指定季度（季度模式时使用）：春、夏、秋、冬
    "season": None,
    
    # 年份范围（全量模式时使用）
    "year_range": {"start": 2013, "end": 2025},
    
    # 季度列表
    "seasons": ["春", "夏", "秋", "冬"],
    
    # 增量爬取配置
    "incremental": {
        "enabled": False,
        "last_crawl_time": None,
        "check_interval": 3600,  # 1小时
    },
    
    # API接口配置
    "api": {
        "enabled": True,
        "timeout": 30,
        "retry_times": 3,
    },
    
    # 动态页面解析配置（API失败时的降级方案）
    "dynamic_parser": {
        "enabled": True,
        "wait_time": 3,  # 等待页面加载时间
        "timeout": 60,
    },
}
```

### 测试模式配置

```python
# src/config.py
CRAWLER_CONFIG = {
    # 测试模式：限制爬取数量（用于开发和测试）
    "test_mode": False,
    "test_limit": 3,
    
    # 请求延迟（秒）
    "download_delay": 0.2,
    
    # 并发请求数
    "concurrent_requests": 16,
    
    # 重试次数
    "retry_times": 3,
}
```

## 使用场景和最佳实践

### 1. 日常监控和更新

**推荐模式**: 首页模式 + 增量模式

**配置建议**:
```bash
# 定时任务：每天凌晨2点更新
python scripts/run_crawler.py --mode homepage

# 增量更新：每小时检查一次
python scripts/run_crawler.py --mode incremental
```

### 2. 历史数据补全

**推荐模式**: 年份模式或季度模式

**配置建议**:
```bash
# 补全2023年数据
python scripts/run_crawler.py --mode year --year 2023

# 补全特定季度
python scripts/run_crawler.py --mode season --year 2023 --season 春
```

### 3. 首次部署和完整同步

**推荐模式**: 全量模式

**配置建议**:
```bash
# 首次全量爬取
python scripts/run_crawler.py --mode full

# 建议在服务器空闲时间执行
# 可以分批次执行，避免对服务器造成压力
```

### 4. 开发和测试

**推荐模式**: 任意模式 + 测试模式

**配置建议**:
```bash
# 测试首页模式
python scripts/run_crawler.py --test --limit 3

# 测试年份模式
python scripts/run_crawler.py --mode year --year 2024 --test --limit 5

# 测试季度模式
python scripts/run_crawler.py --mode season --year 2024 --season 春 --test --limit 2
```

## 定时任务配置

### 使用APScheduler

```python
# scripts/manage_scheduler.py
from src.core.scheduler import CrawlerScheduler

# 创建调度器
scheduler = CrawlerScheduler()

# 添加定时任务
scheduler.add_job(
    job_id="daily_update",
    name="每日更新",
    cron="0 2 * * *",  # 每天凌晨2点
    mode="homepage",
    enabled=True
)

scheduler.add_job(
    job_id="incremental_update",
    name="增量更新",
    cron="0 */2 * * *",  # 每2小时
    mode="incremental",
    enabled=True
)

scheduler.add_job(
    job_id="weekly_full_sync",
    name="每周全量同步",
    cron="0 3 * * 0",  # 每周日凌晨3点
    mode="full",
    enabled=False  # 默认关闭，需要时手动开启
)
```

### 使用crontab

```bash
# 编辑crontab
crontab -e

# 添加定时任务
# 每天凌晨2点执行首页模式更新
0 2 * * * cd /path/to/IKuYo && python scripts/run_crawler.py --mode homepage

# 每2小时执行增量更新
0 */2 * * * cd /path/to/IKuYo && python scripts/run_crawler.py --mode incremental

# 每周日凌晨3点执行全量同步
0 3 * * 0 cd /path/to/IKuYo && python scripts/run_crawler.py --mode full
```

## 错误处理和故障排除

### 常见问题

1. **API接口失败**
   - 系统会自动降级到动态页面解析
   - 检查网络连接和代理设置
   - 查看日志了解具体错误

2. **数据重复**
   - 系统内置去重机制
   - 检查去重Pipeline是否正常工作
   - 查看去重统计信息

3. **爬取速度慢**
   - 调整并发请求数
   - 检查网络延迟
   - 考虑使用代理

4. **内存占用高**
   - 减少并发请求数
   - 启用测试模式限制数据量
   - 定期清理缓存

### 日志分析

```bash
# 查看详细日志
python scripts/run_crawler.py --log-level DEBUG

# 查看特定模式的日志
python scripts/run_crawler.py --mode year --year 2024 --log-level INFO

# 保存日志到文件
python scripts/run_crawler.py --mode homepage > crawl.log 2>&1
```

### 性能优化

1. **调整并发设置**
   ```python
   # src/config.py
   CRAWLER_CONFIG = {
       "concurrent_requests": 32,  # 增加并发数
       "download_delay": 0.1,     # 减少延迟
   }
   ```

2. **启用缓存**
   ```python
   # src/crawler/settings.py
   HTTPCACHE_ENABLED = True
   HTTPCACHE_EXPIRATION_SECS = 3600
   ```

3. **使用代理池**
   ```python
   # src/config.py
   PROXY_CONFIG = {
       "enabled": True,
       "proxy_list": ["http://proxy1:port", "http://proxy2:port"],
   }
   ```

## 数据输出和存储

### 输出格式

系统支持多种输出格式：

1. **JSON格式** (默认)
   ```bash
   python scripts/run_crawler.py --output data/output/anime.json
   ```

2. **CSV格式**
   ```bash
   python scripts/run_crawler.py --output data/output/anime.csv
   ```

3. **数据库存储** (默认)
   - SQLite数据库存储在 `data/database/ikuyo.db`
   - 自动创建表结构和索引

### 数据验证

```bash
# 验证数据完整性
python scripts/validate_data.py

# 检查数据统计
python scripts/data_stats.py
```

## 总结

IKuYo 爬虫系统提供了灵活的多种爬取模式，可以根据不同的使用场景选择合适的策略：

- **首页模式**: 适合日常监控和快速更新
- **年份/季度模式**: 适合历史数据补全和精确控制
- **全量模式**: 适合首次部署和完整数据同步
- **增量模式**: 适合频繁更新和资源优化

通过合理的配置和定时任务设置，可以实现高效、稳定的动画数据采集系统。 