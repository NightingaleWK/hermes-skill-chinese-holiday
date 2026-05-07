# Chinese Holiday (chinese-holiday)

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill for querying Chinese holidays and workdays, with support for adjusted workdays (调休).

## Features

- **Accurate Chinese calendar** — respects State Council holiday announcements and adjusted workdays
- **Multi-source fallback** — bitefu API → timor.tech API → local cache → weekday fallback
- **Zero-dependency script** — pure Python stdlib, no pip install needed
- **Dual output modes** — plain text for cron, structured JSON for agent consumption
- **Auto-caching** — fetches full year data once, silently refreshes every 30 days
- **Check-in reminders** — built-in cron setup for morning/evening workday check-in notifications

## Quick Start

### 1. Deploy the script

```bash
cp scripts/checkin-reminder.py ~/.hermes/scripts/
```

### 2. Query from a conversation

```
> 今天上班吗？
```

Hermes will load this skill and run:

```bash
python3 ~/.hermes/scripts/checkin-reminder.py --json
```

Returns:
```json
{"date": "2026-05-08", "is_workday": true, "weekday": "Friday", "weekday_cn": "周五", "source": "cache"}
```

### 3. Set up auto check-in reminders

Ask Hermes to create two cron jobs with this skill loaded:

- **08:30** — morning check-in (workdays only)
- **17:30** — evening check-in (workdays only)

## Architecture

```
Cron trigger (08:30 / 17:30 daily)
       │
       ▼
   Hermes Agent
       │
       ├── Loads chinese-holiday skill
       ├── Runs checkin-reminder.py --json
       │     ├── ① Local cache (zero network)
       │     ├── ② bitefu API
       │     ├── ③ timor.tech API
       │     └── ④ Mon-Fri fallback
       └── Parses JSON result
             ├── is_workday=true  → pushes reminder
             └── is_workday=false → silent
```

## Data Sources

| Source | Description | Daily Limit |
|--------|-------------|-------------|
| Local cache | timor.tech year-endpoint, auto-refreshed | Unlimited |
| [bitefu](https://tool.bitefu.net/jiari/) | Former Baidu Holiday API | 10k/IP |
| [timor.tech](https://timor.tech/api/holiday/) | Free holiday API | 10k/IP |

All APIs are free and require no registration.

## License

MIT
