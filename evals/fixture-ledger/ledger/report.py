from collections import defaultdict

from ledger.store import Entry


def totals_by_account(entries: list[Entry]) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for e in entries:
        out[e.account] += e.amount_cents
    return dict(out)


def render(totals: dict[str, int]) -> str:
    return "\n".join(f"{acct}\t{cents / 100:.2f}" for acct, cents in sorted(totals.items()))
