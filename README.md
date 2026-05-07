# Chinese Holiday（中国节假日查询）

[Hermes Agent](https://github.com/NousResearch/hermes-agent) 技能，用于查询中国大陆节假日和工作日，支持国务院调休安排。

## 功能

- **中国节假日日历** — 跟随国务院公告，识别调休上班日
- **多源容灾** — bitefu API → timor.tech API → 本地缓存 → 周一至周五硬兜底
- **零依赖脚本** — 纯 Python 标准库，无需 pip install
- **双输出模式** — 纯文本（cron 直推）/ 结构化 JSON（Agent 消费）
- **自动缓存** — 首次运行拉取全年数据，每 30 天静默刷新
- **打卡提醒** — 内置 cron 部署指引，工作日上午/下午自动推送

## 快速开始

### 1. 部署脚本

```bash
cp scripts/checkin-reminder.py ~/.hermes/scripts/
```

### 2. 对话中查询

```
> 今天上班吗？
```

Hermes 加载本 skill 后会自动运行：

```bash
python3 ~/.hermes/scripts/checkin-reminder.py --json
```

返回：
```json
{
  "date": "2026-05-08",
  "is_workday": true,
  "weekday": "Friday",
  "weekday_cn": "周五",
  "source": "cache"
}
```

### 3. 部署自动打卡提醒

让 Hermes 创建两个定时任务，加载本 skill：

- **08:30** — 上班打卡提醒（仅工作日）
- **17:30** — 下班打卡提醒（仅工作日）

## 架构

```
定时任务（每天 08:30 / 17:30）
       │
       ▼
   Hermes Agent
       │
       ├── 加载 chinese-holiday skill
       ├── 运行 checkin-reminder.py --json
       │     ├── ① 本地缓存（零网络）
       │     ├── ② bitefu API
       │     ├── ③ timor.tech API
       │     └── ④ 周一至周五（硬兜底）
       └── 解析 JSON 结果
             ├── is_workday=true  → 推送提醒
             └── is_workday=false → 静默
```

## 节假日判断

| bitefu | timor.tech | 含义 | 是否提醒 |
|--------|-----------|------|----------|
| type=0 | type=0 | 普通工作日 | ✅ |
| — | type=3 | 调休上班（周末补班） | ✅ |
| type=1 | type=1 | 周末双休 | ❌ |
| type=2 | type=2 | 法定节假日 | ❌ |

## 数据源

| 数据源 | 说明 | 日限额 |
|--------|------|--------|
| 本地缓存 | timor.tech 年接口一次性拉取 | 无限制 |
| [bitefu](https://tool.bitefu.net/jiari/) | 原百度节假日 API 作者独立运营 | 1 万次/天/IP |
| [timor.tech](https://timor.tech/api/holiday/) | 最良心的免费节假日 API | 1 万次/天/IP |

全部免费、无需注册。正常情况下全年网络调用不超过 12 次。

## 许可证

MIT
