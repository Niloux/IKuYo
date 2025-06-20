# 定时任务调度用法说明

本项目内置定时任务调度功能，支持自动化定时采集番剧资源。

## 1. 调度原理简介
- 基于 APScheduler 实现，支持 cron 表达式灵活配置采集时间。
- 通过 `scripts/manage_scheduler.py` 脚本进行任务管理（启动、查看状态、测试等）。
- 所有调度参数集中在 `config.yaml` 文件中配置。

## 2. config.yaml 相关字段
```yaml
scheduler:
  enabled: true                # 是否启用定时任务
  default_cron: "0 2 * * *"    # 默认 cron 表达式（每天凌晨2点）
  timezone: Asia/Shanghai      # 时区设置
  jobs:
    - id: mikan_crawler
      name: Mikan爬虫定时任务
      cron: "0 2 * * *"        # cron 表达式
      enabled: true
      description: 定时爬取Mikan Project动漫资源
      mode: homepage           # 可选：homepage/year/season/full/incremental
  scheduler_settings:
    job_defaults:
      coalesce: false
      max_instances: 1
      misfire_grace_time: 300
```
- 可为每个任务单独设置 cron、模式、描述等。
- 支持多任务并行配置。

## 3. manage_scheduler.py 脚本用法
- 启动定时任务调度器：
  ```bash
  python scripts/manage_scheduler.py start
  ```
- 查看任务状态和配置：
  ```bash
  python scripts/manage_scheduler.py status
  ```
- 测试执行一次采集任务：
  ```bash
  python scripts/manage_scheduler.py test
  ```
- 查看帮助信息：
  ```bash
  python scripts/manage_scheduler.py help
  ```

## 4. 配置样例
- 每天凌晨2点自动采集首页推荐番剧：
  ```yaml
  jobs:
    - id: mikan_crawler
      name: Mikan爬虫定时任务
      cron: "0 2 * * *"
      enabled: true
      mode: homepage
  ```
- 每周一凌晨3点全量采集：
  ```yaml
  jobs:
    - id: full_crawler
      name: 全量采集任务
      cron: "0 3 * * 1"
      enabled: true
      mode: full
  ```

## 5. 常见问题
- **定时任务未执行？**
  - 检查`scheduler.enabled`是否为`true`。
  - 检查 cron 表达式是否正确。
  - 查看日志（data/logs/）获取详细报错信息。
- **如何停止调度器？**
  - 直接 Ctrl+C 终止进程即可。
- **如何修改任务时间？**
  - 编辑 config.yaml 中对应 job 的 cron 字段，重启调度器生效。
- **支持哪些 cron 表达式？**
  - 标准 5 字段格式：分 时 日 月 周
  - 例："0 2 * * *" 表示每天2点

如有更多问题，请查阅项目主页或提交 Issue 反馈。 