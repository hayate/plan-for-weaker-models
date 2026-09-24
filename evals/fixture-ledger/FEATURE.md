# Feature request

Add `--from YYYY-MM-DD` and `--to YYYY-MM-DD` (both optional, inclusive) to the CLI so the report
only counts entries inside that window. A malformed date or a --from later than --to must exit 2
with a clear message on stderr, like the missing-file case. Also add `--by-month`, which groups
totals by (YYYY-MM, account) instead of by account.
