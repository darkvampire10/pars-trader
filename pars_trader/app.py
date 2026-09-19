import json
import logging
import os
import signal
import threading
import time
from pathlib import Path
from .store import Store
from .telegram import Telegram, handle
from .scanner import scan

log = logging.getLogger("pars_trader")


def run():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    owner = int(os.environ.get("TELEGRAM_OWNER_ID", "0"))
    if not token or owner <= 0:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and positive TELEGRAM_OWNER_ID in the server environment.")
    if os.environ.get("TRADING_MODE", "signals") != "signals":
        raise SystemExit("This release supports signals only; real execution is not implemented.")
    folder = Path(os.environ.get("DATA_DIR", "data"))
    folder.mkdir(parents=True, exist_ok=True)
    store = Store(folder / "state.sqlite3")
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    api = Telegram(token)
    symbols = os.environ.get("SYMBOLS", "XAUUSD,EURUSD,GBPUSD,USDJPY,USDCHF,USDCAD,AUDUSD,NZDUSD").split(",")
    symbols = [s.strip() for s in symbols if s.strip()]
    offset = store.get("telegram_offset", 0)
    retry = 1
    while not stop.is_set():
        try:
            updates = api.call("getUpdates", offset=offset, timeout=5, allowed_updates=["message"])
            for update in updates:
                reply = handle(update.get("message", {}), owner, store)
                if reply:
                    api.send(owner, reply)
                offset = update["update_id"]+1
                store.put("telegram_offset", offset)
            now = int(time.time())
            (folder / "heartbeat").write_text(str(now))
            if not store.get("paused", True):
                try:
                    candidates = scan(folder/"market.json", folder/"calendar.json", symbols, now)
                    store.put("scan_status", f"{now}: snapshot checked; candidates={len(candidates)}")
                    for key,payload in candidates:
                        # Persist before delivery: avoids repeated stale signals after restart.
                        # Failed notifications remain visible in /recent (documented at-most-once attempt).
                        if store.add_signal(key,payload,now):
                            api.send(owner,payload["text"])
                except (OSError,ValueError,KeyError,TypeError):
                    store.put("scan_status", f"{now}: waiting for valid market/calendar data")
            retry = 1
        except Exception as exc:
            # Deliberately omit exception content: HTTP errors may contain bot token URL.
            log.warning("Transport/loop failure (%s); retry in %ss", type(exc).__name__,retry)
            stop.wait(retry)
            retry = min(30,retry*2)
    store.db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
