"""Optional READ-ONLY bridge. Run with Windows Python beside MT5 (Wine needs testing).

No order_send, no credentials over Telegram, no public network listener.
Writes market.json atomically to DATA_DIR. On separate hosts transfer via SSH privately.
Install official MetaTrader5 package in that terminal's Python environment first.
"""
import json
import os
from pathlib import Path
import tempfile
import time


def main():
    import MetaTrader5 as mt5
    output = Path(os.environ.get("DATA_DIR","data"))
    output.mkdir(parents=True,exist_ok=True)
    mapping = json.loads(os.environ.get("MT5_SYMBOL_MAP",'{"XAUUSD":"XAUUSD","EURUSD":"EURUSD"}'))
    if not mt5.initialize():
        raise SystemExit("MT5 initialize failed; check terminal privately")
    try:
        if not mt5.login(int(os.environ["MT5_LOGIN"]), password=os.environ["MT5_PASSWORD"],server=os.environ["MT5_SERVER"]):
            raise SystemExit("MT5 login failed")
        while True:
            result = {"generated_at":int(time.time()),"symbols":{}}
            for canonical, broker_symbol in mapping.items():
                if not mt5.symbol_select(broker_symbol,True):
                    continue
                tick = mt5.symbol_info_tick(broker_symbol)
                if tick is None:
                    continue
                item = {"bid":tick.bid,"ask":tick.ask,"tick_time":int(tick.time)}
                for label, tf in (("m1",mt5.TIMEFRAME_M1),("m5",mt5.TIMEFRAME_M5),("m15",mt5.TIMEFRAME_M15)):
                    rows = mt5.copy_rates_from_pos(broker_symbol,tf,1,200)
                    if rows is None:
                        item[label] = []
                    else:
                        item[label] = [{"time":int(r["time"]), **{k:float(r[k]) for k in ("open","high","low","close")}} for r in rows]
                result["symbols"][canonical] = item
            with tempfile.NamedTemporaryFile(mode="w", dir=output,delete=False) as handle:
                json.dump(result,handle)
                temp_path = handle.name
            os.replace(temp_path,output/"market.json")
            time.sleep(3)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
