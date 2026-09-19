import hashlib
import json
from pathlib import Path
from .strategy import Bar, detect
from .news import news_clear


def scan(path, calendar, symbols, now):
    """Read atomic file snapshots exported by the optional MT5 reader.

    Returning candidates is not approval to trade; no account risk/volume is guessed.
    """
    data = json.loads(Path(path).read_text())
    if not 0 <= now-int(data["generated_at"]) <= 15:
        raise ValueError("stale snapshot")
    found = []
    for symbol in symbols:
        item = data["symbols"].get(symbol)
        if not item or not 0 <= now-int(item["tick_time"]) <= 10:
            continue
        if not news_clear(calendar, symbol, now):
            continue
        bars = [[Bar(**b) for b in item[tf]] for tf in ("m1","m5","m15")]
        setup = detect(symbol, *bars, float(item["bid"]), float(item["ask"]), now)
        if setup:
            key = hashlib.sha256(f"v1:{symbol}:{setup.side}:{setup.timestamp}".encode()).hexdigest()
            target_text = " / ".join(f"{p:.5f}" for p in setup.targets)
            text = (f"ستاپ پژوهشی — بدون اجرای سفارش\n{symbol} {setup.side}\n"
                    f"ورود مرجع: {setup.entry:.5f}\nاستاپ: {setup.stop:.5f}\n"
                    f"TP1 / TP2 / TP3: {target_text}\n"
                    "قانون خروج: یک‌سوم در هر تارگت؛ استاپ پس از خروج اول روی ورود\n"
                    "حجم: محاسبه نشده؛ حساب به موتور ریسک متصل نیست\n"
                    "روش: شکست و پولبک | AI: متصل نیست\n"
                    f"زمان UTC Unix: {now} | انقضا: ۶۰ ثانیه")
            found.append((key,{"text":text,"symbol":symbol,"created_at":now,"expires_at":now+60}))
    return found
