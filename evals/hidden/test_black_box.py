"""Eval-owned black-box tests for the implementation stage.

They drive only the CLI surface FEATURE.md defines, so they hold for any plan's
internal contract. The implementer never sees them. Run against an implemented
fixture copy:

    LEDGER_REPO=/path/to/implemented/repo python -m pytest -q evals/hidden

Only what FEATURE.md fixes is asserted. The --by-month line format is left to the
plan, so those tests look for the month, account and amount on one line.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(os.environ.get("LEDGER_REPO", "."))

ROWS = [
    ("2026-01-31", "food", 100),
    ("2026-02-01", "food", 250),
    ("2026-02-15", "rent", 5000),
    ("2026-02-28", "food", 300),
    ("2026-03-01", "food", 700),
    ("2025-02-10", "food", 9900),  # same month, another year: must not merge
]


@pytest.fixture
def csv_path(tmp_path):
    p = tmp_path / "entries.csv"
    shuffled = [ROWS[i] for i in (3, 0, 5, 2, 4, 1)]  # unsorted on purpose
    p.write_text("day,account,amount_cents,memo\n" + "".join(f"{d},{a},{c},x\n" for d, a, c in shuffled))
    return p


def assert_feature_error(r):
    """Exit 2 with the feature's own message: argparse's usage error for an
    unknown flag also exits 2 on stderr, and must not count."""
    assert r.returncode == 2
    assert r.stderr.strip()
    assert "unrecognized arguments" not in r.stderr and "usage:" not in r.stderr
    assert r.stdout == ""


def ledger(*args):
    return subprocess.run(
        [sys.executable, "-m", "ledger.cli", *map(str, args)],
        cwd=REPO, capture_output=True, text=True, timeout=60,
    )


def test_no_flags_unchanged(csv_path):
    r = ledger(csv_path)
    assert r.returncode == 0
    assert r.stdout.splitlines() == ["food\t112.50", "rent\t50.00"]


def test_window_is_inclusive_at_both_ends(csv_path):
    r = ledger("--from", "2026-02-01", "--to", "2026-02-28", csv_path)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["food\t5.50", "rent\t50.00"]


def test_from_only_and_to_only(csv_path):
    assert ledger("--from", "2026-03-01", csv_path).stdout.splitlines() == ["food\t7.00"]
    assert ledger("--to", "2025-12-31", csv_path).stdout.splitlines() == ["food\t99.00"]


@pytest.mark.parametrize("bad", ["2026-13-01", "2026-02-30", "yesterday", "20260201"])
def test_malformed_date_exits_2_on_stderr(csv_path, bad):
    assert_feature_error(ledger("--from", bad, csv_path))


def test_from_after_to_exits_2(csv_path):
    assert_feature_error(ledger("--from", "2026-03-01", "--to", "2026-02-01", csv_path))


def test_missing_file_still_exits_2(tmp_path):
    r = ledger(tmp_path / "nope.csv")
    assert r.returncode == 2
    assert "no such file" in r.stderr


def _line_with(lines, *tokens):
    return [line for line in lines if all(t in line for t in tokens)]


def test_by_month_groups_by_month_and_account(csv_path):
    r = ledger("--by-month", csv_path)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert _line_with(lines, "2026-02", "food", "5.50")
    assert _line_with(lines, "2026-02", "rent", "50.00")
    assert _line_with(lines, "2026-01", "food", "1.00")
    assert _line_with(lines, "2025-02", "food", "99.00")  # year kept apart
    assert len(lines) == 5


def test_by_month_respects_the_window(csv_path):
    r = ledger("--by-month", "--from", "2026-02-15", "--to", "2026-03-01", csv_path)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert _line_with(lines, "2026-02", "food", "3.00")
    assert _line_with(lines, "2026-02", "rent", "50.00")
    assert _line_with(lines, "2026-03", "food", "7.00")
    assert len(lines) == 3
