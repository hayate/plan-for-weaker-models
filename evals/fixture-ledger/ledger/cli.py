import argparse
import sys
from pathlib import Path

from ledger import report, store


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ledger")
    p.add_argument("csv", type=Path)
    args = p.parse_args(argv)
    try:
        entries = store.load(args.csv)
    except FileNotFoundError:
        print(f"ledger: no such file: {args.csv}", file=sys.stderr)
        return 2
    print(report.render(report.totals_by_account(entries)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
