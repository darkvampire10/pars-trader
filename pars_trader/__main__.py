import argparse
import json
from .core import Setup, PaperPosition
from . import __version__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["demo","run","version"], nargs="?", default="demo")
    args = parser.parse_args()
    if args.command == "version":
        print(__version__)
    elif args.command == "run":
        from .app import run
        run()
    else:
        position = PaperPosition(Setup("SYNTHETIC", "buy", 100., 99., 0))
        result = {"mode":"synthetic demonstration, not a market signal", "targets":position.setup.targets, "events":[]}
        for bid in (101.,102.,103.):
            result["events"].extend(position.quote(bid,bid+.01))
        result["gross_pnl_r"] = round(position.pnl_r,6)
        result["costs_included"] = False
        print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
