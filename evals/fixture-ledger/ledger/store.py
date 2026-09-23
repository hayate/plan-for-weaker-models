import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    day: date
    account: str
    amount_cents: int
    memo: str


def load(path: Path) -> list[Entry]:
    with path.open(newline="") as fh:
        return [
            Entry(date.fromisoformat(r["day"]), r["account"], int(r["amount_cents"]), r["memo"])
            for r in csv.DictReader(fh)
        ]
