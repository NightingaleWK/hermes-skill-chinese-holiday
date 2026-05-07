     1|#!/usr/bin/env python3
     2|"""
     3|中国节假日查询脚本
     4|判断今天是否为工作日（含国务院调休），支持两种输出格式。
     5|
     6|用法:
     7|  python checkin-reminder.py             # 纯文本（cron no_agent 直推）
     8|  python checkin-reminder.py --json      # JSON 输出（供 Agent 消费）
     9|
    10|数据源优先级:
    11|  1. 本地缓存   (零网络，每 30 天自动刷新)
    12|  2. bitefu API (主力在线)
    13|  3. timor.tech  (备用在线)
    14|  4. 周一至周五  (硬兜底)
    15|"""
    16|
    17|import argparse
    18|import json
    19|import os
    20|import sys
    21|import urllib.request
    22|from datetime import date, datetime, timedelta
    23|
    24|CACHE_DIR = os.path.expanduser("~/.hermes/cache")
    25|
    26|
    27|def _cache_path(year: int) -> str:
    28|    return os.path.join(CACHE_DIR, f"holiday-{year}.json")
    29|
    30|
    31|def _load_cache(year: int) -> tuple[set | None, bool]:
    32|    try:
    33|        with open(_cache_path(year)) as f:
    34|            data = json.load(f)
    35|        if data.get("year") != year or "non_workdays" not in data:
    36|            return None, True
    37|        needs_refresh = True
    38|        fetched = data.get("fetched_at", "")
    39|        if fetched:
    40|            try:
    41|                age = datetime.now() - datetime.fromisoformat(fetched)
    42|                needs_refresh = age.days > 30
    43|            except ValueError:
    44|                pass
    45|        return set(data["non_workdays"]), needs_refresh
    46|    except Exception:
    47|        return None, True
    48|
    49|
    50|def _save_cache(year: int, non_workdays: set) -> None:
    51|    os.makedirs(CACHE_DIR, exist_ok=True)
    52|    cache = {
    53|        "year": year,
    54|        "non_workdays": sorted(non_workdays),
    55|        "fetched_at": datetime.now().isoformat(),
    56|    }
    57|    with open(_cache_path(year), "w") as f:
    58|        json.dump(cache, f, ensure_ascii=False)
    59|
    60|
    61|def _refresh_cache(year: int) -> bool:
    62|    try:
    63|        url = f"https://timor.tech/api/holiday/year/{year}/"
    64|        req = urllib.request.Request(
    65|            url, headers={"User-Agent": "Mozilla/5.0 (Hermes cache)"}
    66|        )
    67|        with urllib.request.urlopen(req, timeout=10) as resp:
    68|            data = json.loads(resp.read().decode("utf-8"))
    69|        if data.get("code") != 0:
    70|            return False
    71|
    72|        non_workdays: set[str] = set()
    73|        makeup_workdays: set[str] = set()
    74|
    75|        for mmdd, info in data.get("holiday", {}).items():
    76|            if info.get("holiday"):
    77|                non_workdays.add(mmdd)
    78|            elif info.get("after") is not None:
    79|                makeup_workdays.add(mmdd)
    80|
    81|        d = date(year, 1, 1)
    82|        while d.year == year:
    83|            if d.weekday() >= 5:
    84|                mmdd = d.strftime("%m-%d")
    85|                if mmdd not in makeup_workdays:
    86|                    non_workdays.add(mmdd)
    87|            d += timedelta(days=1)
    88|
    89|        _save_cache(year, non_workdays)
    90|        return True
    91|    except Exception:
    92|        return False
    93|
    94|
    95|def _check_bitefu(date_str: str) -> bool | None:
    96|    try:
    97|        url = f"https://tool.bitefu.net/jiari/?d={date_str}&info=1"
    98|        req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
    99|        with urllib.request.urlopen(req, timeout=5) as resp:
   100|            data = json.loads(resp.read().decode("utf-8"))
   101|        return data.get("type") == 0
   102|    except Exception:
   103|        return None
   104|
   105|
   106|def _check_timor(date_fmt: str) -> bool | None:
   107|    try:
   108|        url = f"https://timor.tech/api/holiday/info/{date_fmt}"
   109|        req = urllib.request.Request(
   110|            url, headers={"User-Agent": "Mozilla/5.0 (Hermes checkin)"}
   111|        )
   112|        with urllib.request.urlopen(req, timeout=5) as resp:
   113|            data = json.loads(resp.read().decode("utf-8"))
   114|        if data.get("code") == 0:
   115|            day_type = data.get("type", {}).get("type", -1)
   116|            return day_type in (0, 3)
   117|    except Exception:
   118|        pass
   119|    return None
   120|
   121|
   122|def check_today() -> dict:
   123|    """查询今天的工作日状态，返回结构化 dict"""
   124|    today = date.today()
   125|    today_str = today.strftime("%Y%m%d")
   126|    today_fmt = today.strftime("%Y-%m-%d")
   127|    mmdd = today.strftime("%m-%d")
   128|    year = today.year
   129|
   130|    source = "unknown"
   131|    is_wd = False
   132|
   133|    # ① 本地缓存
   134|    cache, needs_refresh = _load_cache(year)
   135|    if cache is not None:
   136|        if needs_refresh:
   137|            _refresh_cache(year)
   138|        is_wd = mmdd not in cache
   139|        source = "cache"
   140|        return {
   141|            "date": today_fmt,
   142|            "is_workday": is_wd,
   143|            "weekday": today.strftime("%A"),
   144|            "weekday_cn": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()],
   145|            "source": source,
   146|        }
   147|
   148|    # ② bitefu
   149|    result = _check_bitefu(today_str)
   150|    if result is not None:
   151|        _refresh_cache(year)
   152|        is_wd = result
   153|        source = "bitefu"
   154|        return {
   155|            "date": today_fmt,
   156|            "is_workday": is_wd,
   157|            "weekday": today.strftime("%A"),
   158|            "weekday_cn": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()],
   159|            "source": source,
   160|        }
   161|
   162|    # ③ timor.tech
   163|    result = _check_timor(today_fmt)
   164|    if result is not None:
   165|        _refresh_cache(year)
   166|        is_wd = result
   167|        source = "timor.tech"
   168|        return {
   169|            "date": today_fmt,
   170|            "is_workday": is_wd,
   171|            "weekday": today.strftime("%A"),
   172|            "weekday_cn": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()],
   173|            "source": source,
   174|        }
   175|
   176|    # ④ 重建缓存
   177|    if _refresh_cache(year):
   178|        cache, _ = _load_cache(year)
   179|        if cache is not None:
   180|            is_wd = mmdd not in cache
   181|            source = "cache(rebuilt)"
   182|            return {
   183|                "date": today_fmt,
   184|                "is_workday": is_wd,
   185|                "weekday": today.strftime("%A"),
   186|                "weekday_cn": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()],
   187|                "source": source,
   188|            }
   189|
   190|    # ⑤ 硬兜底
   191|    is_wd = today.weekday() < 5
   192|    source = "fallback"
   193|    return {
   194|        "date": today_fmt,
   195|        "is_workday": is_wd,
   196|        "weekday": today.strftime("%A"),
   197|        "weekday_cn": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()],
   198|        "source": source,
   199|    }
   200|
   201|
   202|def main():
   203|    parser = argparse.ArgumentParser(description="中国节假日/工作日查询")
   204|    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
   205|    args = parser.parse_args()
   206|
   207|    result = check_today()
   208|    is_wd = result["is_workday"]
   209|
   210|    if args.json:
   211|        print(json.dumps(result, ensure_ascii=False))
   212|    else:
   213|        # 纯文本模式：工作日输出提醒，非工作日静默
   214|        if is_wd:
   215|            hour = datetime.now().hour
   216|            if hour < 12:
   217|                print("⏰ 上班打卡提醒！请在 9:00 前完成打卡。")
   218|            else:
   219|                print("⏰ 下班打卡提醒！请在 17:30 完成打卡。")
   220|
   221|
   222|if __name__ == "__main__":
   223|    main()
   224|