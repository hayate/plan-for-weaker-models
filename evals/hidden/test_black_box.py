"""Eval-owned black-box tests for the implementation stage.

They drive only the CLI surface FEATURE.md defines, so they hold for any plan's
internal contract. The implementer never sees them. Run against an implemented
fixture copy:

    LEDGER_REPO=/path/to/implemented/repo python -m pytest -q evals/hidden

Only what FEATURE.md fixes is asserted. The --by-month line format is left to the
plan, so each output line is parsed into a (month, account) -> amount record, with
any whitespace, comma, semicolon or pipe as the separator, and the whole mapping is
compared exactly.
"""
import os
import re
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
    """Exit 2 with a message on stderr. argparse rejecting --from as an unknown
    option also exits 2 on stderr, so that signature must not count; a validation
    error raised through argparse (parser.error, a type= validator) is fine."""
    assert r.returncode == 2
    assert r.stderr.strip()
    assert "unrecognized arguments" not in r.stderr
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


MONTH = re.compile(r"\d{4}-\d{2}")
AMOUNT = re.compile(r"-?\d+\.\d{2}")


def by_month(stdout):
    """(month, account) -> amount for every output line that names a month."""
    records = {}
    for line in stdout.splitlines():
        tokens = [t for t in re.split(r"[\s,;|]+", line.strip()) if t]
        months = [t for t in tokens if MONTH.fullmatch(t)]
        if not months:
            continue  # a header or blank line
        amounts = [t for t in tokens if AMOUNT.fullmatch(t)]
        rest = [t for t in tokens if not MONTH.fullmatch(t) and not AMOUNT.fullmatch(t)]
        assert len(months) == 1 and len(amounts) == 1 and len(rest) == 1, f"unparseable line: {line!r}"
        key = (months[0], rest[0])
        assert key not in records, f"duplicate group: {key}"
        records[key] = amounts[0]
    return records


def test_by_month_groups_by_month_and_account(csv_path):
    r = ledger("--by-month", csv_path)
    assert r.returncode == 0, r.stderr
    assert by_month(r.stdout) == {
        ("2025-02", "food"): "99.00",  # same month, other year: kept apart
        ("2026-01", "food"): "1.00",
        ("2026-02", "food"): "5.50",
        ("2026-02", "rent"): "50.00",
        ("2026-03", "food"): "7.00",
    }


def test_by_month_respects_the_window(csv_path):
    r = ledger("--by-month", "--from", "2026-02-15", "--to", "2026-03-01", csv_path)
    assert r.returncode == 0, r.stderr
    assert by_month(r.stdout) == {
        ("2026-02", "food"): "3.00",
        ("2026-02", "rent"): "50.00",
        ("2026-03", "food"): "7.00",
    }
