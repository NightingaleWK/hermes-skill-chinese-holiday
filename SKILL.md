     1|---
     2|name: chinese-holiday
     3|description: "Use when asking about Chinese holidays, workdays, or setting up workday-based reminders. Covers China's official holiday calendar with adjusted workdays (调休). Supports both conversational queries and cron-based automated check-in reminders."
     4|version: 1.0.0
     5|author: Hermes Agent
     6|license: MIT
     7|metadata:
     8|  hermes:
     9|    tags: [china, holidays, workday, calendar, reminder, productivity]
    10|    related_skills: [hermes-agent]
    11|---
    12|
    13|# 中国节假日查询 (chinese-holiday)
    14|
    15|判断任意日期是否为中国大陆工作日（含国务院调休安排）。支持日常查询和定时打卡提醒两种使用场景。
    16|
    17|## 数据源
    18|
    19|| 数据源 | 说明 | 限额 | 覆盖 |
    20||--------|------|------|------|
    21|| 本地缓存 | timor.tech 年接口一次性拉取，每 30 天自动刷新 | 无 | 当前年份 |
    22|| [bitefu](https://tool.bitefu.net/jiari/) | 原百度节假日 API 作者独立运营 | 1 万次/天/IP | 2009-2026 |
    23|| [timor.tech](https://timor.tech/api/holiday/) | 可能是最良心的免费节假日 API | 1 万次/天/IP | 依国务院更新 |
    24|
    25|两个在线 API 均免费、无需注册。
    26|
    27|## 使用方式
    28|
    29|### 场景一：对话中查询
    30|
    31|当用户问"今天上班吗""五一放几天""这周六补班吗"等问题时：
    32|
    33|```bash
    34|python3 ~/.hermes/scripts/checkin-reminder.py --json
    35|```
    36|
    37|解析输出的 JSON，向用户报告结果。
    38|
    39|**JSON 输出格式：**
    40|```json
    41|{
    42|  "date": "2026-05-07",
    43|  "is_workday": true,
    44|  "weekday": "Thursday",
    45|  "weekday_cn": "周四",
    46|  "source": "cache"
    47|}
    48|```
    49|
    50|| 字段 | 说明 |
    51||------|------|
    52|| `is_workday` | `true`=工作日（含调休上班），`false`=非工作日（周末/节假日） |
    53|| `source` | 数据来源：`cache` / `bitefu` / `timor.tech` / `fallback` |
    54|| `weekday_cn` | 中文星期 |
    55|
    56|### 场景二：自动打卡提醒
    57|
    58|创建两个 cron 任务（Agent 驱动模式）：
    59|
    60|**上班提醒（08:30）：**
    61|```
    62|cronjob create:
    63|  name="上班打卡提醒"
    64|  schedule="30 8 * * *"
    65|  skills=["chinese-holiday"]
    66|  prompt="运行 python3 ~/.hermes/scripts/checkin-reminder.py --json。解析 JSON。如果 is_workday 是 false，你必须输出且只输出一个半角空格（U+0020），不能有任何其他字符。如果 is_workday 是 true，输出：⏰ 上班打卡提醒！请在 9:00 前完成打卡。"
    67|```
    68|
    69|**下班提醒（17:30）：**
    70|```
    71|cronjob create:
    72|  name="下班打卡提醒"
    73|  schedule="30 17 * * *"
    74|  skills=["chinese-holiday"]
    75|  prompt="运行 python3 ~/.hermes/scripts/checkin-reminder.py --json。解析 JSON。如果 is_workday 是 false，你必须输出且只输出一个半角空格（U+0020），不能有任何其他字符。如果 is_workday 是 true，输出：⏰ 下班打卡提醒！请在 17:30 完成打卡。"
    76|```
    77|
    78|**非工作日静默原理：** Agent 输出一个空格，推送后用户几乎无感知。工作日则输出完整提醒。
    79|
    80|### 场景三：查询指定日期
    81|
    82|脚本当前只支持"今天"，但用户对话中可能问历史/未来日期。此时直接用 API：
    83|
    84|**bitefu 单日查询：**
    85|```bash
    86|curl -s "https://tool.bitefu.net/jiari/?d=YYYYMMDD&info=1"
    87|# type: 0=工作日, 1=假日, 2=节日
    88|```
    89|
    90|**timor.tech 单日查询：**
    91|```bash
    92|curl -sL -H "User-Agent: Mozilla/5.0" "https://timor.tech/api/holiday/info/YYYY-MM-DD"
    93|# type.type: 0=工作日, 1=周末, 2=节日, 3=调休上班
    94|```
    95|
    96|### 场景四：部署脚本
    97|
    98|若用户环境缺少脚本：
    99|
   100|```bash
   101|cp ~/.hermes/skills/productivity/chinese-holiday/scripts/checkin-reminder.py ~/.hermes/scripts/
   102|```
   103|
   104|## 节假日判断逻辑
   105|
   106|| bitefu type | timor.tech type | 含义 | 是否工作日 |
   107||------------|-----------------|------|-----------|
   108|| 0 | 0 | 普通工作日 | ✅ |
   109|| — | 3 | 调休（周末上班） | ✅ |
   110|| 1 | 1 | 周末双休 | ❌ |
   111|| 2 | 2 | 法定节假日 | ❌ |
   112|
   113|## 自定义
   114|
   115|修改 `~/.hermes/scripts/checkin-reminder.py`：
   116|- 提醒文字：搜索 `上班打卡提醒` / `下班打卡提醒`
   117|- 刷新周期：搜索 `age.days > 30`
   118|- 上下午判断：`hour < 12` 为上午
   119|
   120|手动刷新缓存：删除 `~/.hermes/cache/holiday-{年份}.json`
   121|
   122|## 常见问题
   123|
   124|**Q: 国务院临时调休？** A: 缓存每 30 天自动刷新。手动加速：删缓存文件。
   125|
   126|**Q: API 全挂？** A: 降级为周一至周五判断，宁可多提醒不漏打卡。
   127|
   128|**Q: 2027 年以后？** A: bitefu 和 timor.tech 覆盖到 2026 年底。数据更新后自动生效；未更新前降级为周一至周五。
   129|
   130|**Q: 只想打一次卡？** A: 删除不需要的 cron 任务即可。
   131|
   132|**Q: 打卡时间怎么改？** A: 改 cron 的 schedule 字段（cron 表达式）。
   133|