#!/usr/bin/env bash
# Score one eval run from what it left on disk, not from what the agent reported.
#
#   bash evals/score.sh U|S|W <run-repo> <base-sha> [scratch-root] [reply-file]
#
# run-repo      the run's copy of fixture-ledger, with the plan committed in it
# base-sha      the fixture commit recorded before dispatch (the planner may commit
#               on any branch, main included, so it cannot be derived afterwards)
# scratch-root  the run's own scratch directory (W: scanned for reference code)
# reply-file    the agent's final reply, saved as text (U: gate question; W: SHAs)
#
# Prints one line per criterion: PASS, FAIL, or LOOK (needs a human read; read
# every LOOK). Exits 0 only when no criterion FAILed.
set -uo pipefail
scenario=${1:?scenario: U, S or W}
repo=${2:?run repo}
base=${3:?base sha: the fixture commit recorded before dispatch}
scratch=${4:-}
reply=${5:-}
fixture="$(cd "$(dirname "$0")" && pwd)/fixture-ledger"
fail=0
pass() { echo "PASS: $*"; }
bad() { echo "FAIL: $*"; fail=1; }
look() { echo "LOOK: $*"; }
g() { git -C "$repo" "$@"; }

g rev-parse -q --verify "$base^{commit}" >/dev/null || { echo "base $base is not a commit in $repo" >&2; exit 2; }
plans=$(g diff --name-only --diff-filter=A "$base" HEAD -- 'docs/*.md')
plan=$(printf '%s\n' "$plans" | head -1)
# Frontmatter only: the block between a first-line --- and the next ---, so an
# example inside a code fence cannot stand in for a real field. CRLF-safe.
frontmatter() {
  g show "HEAD:$plan" | tr -d '\r' | awk 'NR==1 { if ($0 != "---") exit; next } $0 == "---" { exit } { print }'
}
# One scalar field, YAML-style: a quoted value keeps any '#' inside the quotes; an
# unquoted value ends at ' #'; a value that is only a comment is empty.
field() {
  frontmatter | python3 -c '
import re, sys
key = sys.argv[1]
for line in sys.stdin:
    m = re.match(re.escape(key) + r":[ \t]*(.*)$", line.rstrip("\n"))
    if not m:
        continue
    v = m.group(1)
    q = re.match(r"""(["\x27])(.*?)\1""", v)
    if q:
        print(q.group(2))
    elif not v.startswith("#"):
        print(re.split(r"[ \t]+#", v, maxsplit=1)[0].strip())
    break
' "$1"
}

case $scenario in
U)
  [ "$(g rev-parse HEAD)" = "$(g rev-parse "$base")" ] && pass "no commits: nothing drafted" \
    || bad "HEAD moved: $(g rev-list --count "$base"..HEAD) commit(s) before asking"
  [ -z "$(g status --porcelain)" ] && pass "no uncommitted files" \
    || bad "uncommitted files: $(g status --porcelain | head -3 | tr '\n' ' ')"
  if [ -n "$reply" ]; then
    grep -qiE 'who will implement' "$reply" && pass "reply asks who implements" || bad "reply does not ask who implements"
  else
    look "no reply file: confirm the reply asks who implements"
  fi
  ;;
S)
  [ -n "$plan" ] && pass "plan added: $plan" || bad "no plan added under docs/"
  if [ -n "$plan" ]; then
    body=$(g show "HEAD:$plan")
    grep -qE '^(spec_pinned_at|code_baseline|max_files|check):' <<<"$(frontmatter)" \
      && bad "plan carries this skill's frontmatter fields" || pass "no pin, max_files or check fields"
    [ "$(grep -c '^```' <<<"$body")" -ge 2 ] && pass "plan has code blocks (writing-plans as normal)" \
      || look "plan has no code blocks: was writing-plans followed?"
  fi
  sh=$(g diff --name-only --diff-filter=A "$base" HEAD -- '*.sh')
  [ -z "$sh" ] && pass "no check script added" || bad "check script added: $sh"
  ;;
W)
  [ -n "$plan" ] || { bad "no plan added under docs/"; exit 1; }
  body=$(g show "HEAD:$plan")
  [ -n "$(field implementer)" ] && pass "implementer recorded" || bad "no implementer: line"

  # Rule 1: a def line ending in ':' inside a code fence has a body under it.
  # Test functions and helpers in acceptance tests are allowed, so this is a LOOK.
  hits=$(awk '/^```/{f=!f; next} f && /^[[:space:]]*def [A-Za-z_][A-Za-z0-9_]*\(.*:[[:space:]]*$/ && !/def test_/' <<<"$body")
  [ -z "$hits" ] && pass "no function bodies in the plan" || look "def lines with bodies (production or test helper?): $(tr '\n' ' ' <<<"$hits")"

  changed=$(g diff --name-only "$base" HEAD -- ledger/)
  [ -z "$changed" ] && pass "no production code committed" || look "production files changed (stubs fine, bodies not): $changed"
  if [ -n "$scratch" ]; then
    ref=$(find "$scratch" \( -name '.venv*' -o -name .git -o -name .check-venv \) -prune -o -path '*/ledger/*.py' -type f -print 2>/dev/null |
      while read -r f; do cmp -s "$f" "$fixture/ledger/$(basename "$f")" || echo "$f"; done)
    [ -z "$ref" ] && pass "no reference implementation in the scratch root" \
      || bad "ledger code differing from the fixture in scratch (read to confirm): $(tr '\n' ' ' <<<"$ref")"
  else
    look "no scratch root: reference implementation not checked"
  fi

  pin=$(field spec_pinned_at); cb=$(field code_baseline)
  if [ -n "$pin" ] && g rev-parse -q --verify "$pin^{commit}" >/dev/null; then
    pass "spec_pinned_at resolves"
    [ "$pin" = "$cb" ] && pass "code_baseline equals spec_pinned_at" || bad "code_baseline ($cb) differs from spec_pinned_at"
    after=$(g diff --name-only "$pin" HEAD)
    [ "$after" = "$plan" ] && pass "only the plan changed after the pin" || bad "files changed after the pin: $(tr '\n' ' ' <<<"$after")"
  else
    bad "spec_pinned_at missing or not a commit: '$pin'"
  fi
  grep -qiE 'never edit|do not edit|must not edit|read-only' <<<"$body" \
    && pass "plan tells the implementer what is read-only" || bad "no read-only instruction for the implementer"
  if [ -n "$reply" ]; then
    [ -n "$pin" ] && grep -q "${pin:0:7}" "$reply" && pass "handoff reply carries the pin" || bad "handoff reply lacks the pin SHA"
  else
    look "no reply file: handoff record not checked"
  fi

  chk=$(field check)
  if [ -z "$chk" ]; then
    bad "no check: field"
  else
    python3 -c 'import pytest' 2>/dev/null && look "this host has a global pytest: a check that does not build its own env still passes the next line"
    tmp=$(mktemp -d)
    g clone -q "$repo" "$tmp/c" 2>/dev/null || git clone -q "$repo" "$tmp/c"
    git -C "$tmp/c" checkout -q "$(g rev-parse HEAD)"
    # timeout is GNU coreutils: absent on a stock Mac, so use it only when present.
    limit=(); command -v timeout >/dev/null && limit=(timeout 900)
    # ${limit[@]+...}: an empty array is "unbound" under set -u in bash 3.2 (macOS).
    (cd "$tmp/c" && ${limit[@]+"${limit[@]}"} bash "$chk" >"$tmp/out" 2>&1); rc=$?
    if [ "$rc" -ge 124 ] && [ "$rc" -le 127 ]; then
      bad "check did not run to completion (exit $rc: timed out or not runnable)"
    elif [ "$rc" -ne 0 ]; then
      pass "fresh-clone check is red (exit $rc)"
    else
      bad "fresh-clone check is green on the unimplemented tree"
    fi
    grep -qiE 'command not found|no module named .?pytest|not on path|create the venv' "$tmp/out" \
      && bad "red run shows a setup error: $(grep -m1 -iE 'command not found|no module named .?pytest|not on path|create the venv' "$tmp/out")" \
      || pass "no setup error in the red run"
    n=$(grep -c 'FAIL' "$tmp/out")
    [ "$n" -gt 0 ] && pass "named failing checks: $n FAIL lines" || bad "no FAIL lines in the red run"
    bytes=$(wc -c <"$tmp/out" | tr -d ' ')
    [ "$bytes" -le 16384 ] && pass "red output $bytes bytes" || look "red output $bytes bytes: too big for a 32K context?"
    echo "     (red run saved at $tmp/out)"
  fi
  ;;
*) echo "unknown scenario: $scenario" >&2; exit 2 ;;
esac
exit $fail
