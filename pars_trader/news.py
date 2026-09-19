"""File calendar interface. Absence, stale coverage or invalid timestamps BLOCK."""
import json
from pathlib import Path


def news_clear(path, symbol, now, window=900):
    try:
        data = json.loads(Path(path).read_text())
        generated = int(data["generated_at"])
        if not 0 <= now-generated <= 3600:
            return False
        if int(data["coverage_start"]) > now-window or int(data["coverage_end"]) < now+window:
            return False
        currencies = {symbol[:3], symbol[3:6]}
        if not currencies <= set(data["currencies"]):
            return False
        for event in data["events"]:
            timestamp = int(event["time"])
            if event["currency"] in currencies and event["impact"] == "high" and abs(timestamp-now) <= window:
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False
