from datetime import date

from ledger.report import render, totals_by_account
from ledger.store import Entry


def test_totals_sum_per_account():
    es = [Entry(date(2026, 1, 1), "food", 500, ""), Entry(date(2026, 1, 2), "food", 250, "")]
    assert totals_by_account(es) == {"food": 750}


def test_render_sorted():
    assert render({"b": 100, "a": 250}) == "a\t2.50\nb\t1.00"
