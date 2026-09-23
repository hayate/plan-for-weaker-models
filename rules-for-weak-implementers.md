# Rules for a weak implementer

Read this in full when the gate in SKILL.md says apply, before drafting the plan.

## Where this overrides writing-plans

writing-plans still runs the plan: exact paths, exact commands, the header, the
user's review. It is overridden on these points and no others:

- **Production code.** The plan names contracts (Rule 1) and contains no production
  function bodies. writing-plans' "code blocks required for code steps" and its
  placeholder scan do not apply to production code: a contract step (signature,
  error type, call sites, test file) is complete, not a placeholder.
- **Tests.** The acceptance tests are yours, written in full, in files the
  implementer never edits: they define done (Rule 2). A task's red step is
  `check.sh <task>` failing, not the implementer writing a failing test. The
  implementer may add its own unit tests in the test file the contract names.
- **Task size.** Rule 4, not writing-plans' grouping.
- **Plan header.** Replace the sub-skill line with the `implementer:` line and the
  check command, since a local model has no skills to load. Keep it when the
  implementer is subagent-driven-development.
- **Execution handoff.** The gate already settled it; use writing-plans' "method
  already supplied" wording.
- **Constraints that cannot be scripted.** They are not acceptance criteria. List
  them under a "Reviewer checklist" heading for the reviewer, never as done
  criteria for the implementer.

## Rule 1: name the contract, not the body

The plan fixes anchors. It does not write code.

Name: file path, function or class name, full signature with types, the error type
raised, the constant and where it lives, the call sites that change, the test file.

Do not write: the function body, the algorithm, the loop, the query.

Discriminator for any line you are about to add: if removing it would still let the
implementer produce a wrong-but-plausible *interface*, keep it. If removing it only
rules out one of several correct ways to satisfy a contract you already named, cut
it.

- Too vague: "handle errors appropriately". That is an empty slot, and the weak
  model fills it with a bare except that logs and continues.
- Too far: ten lines of pseudocode for the body. You are now implementing on the
  expensive model and paying for it twice.
- Right: "`parse_window(raw: str) -> tuple[date, date]` in `lib/window.py`, raises
  `ValueError` on unparseable input. Both existing call sites already catch
  `ValueError`; do not swallow it inside the helper. Unit tests go in
  `tests/test_window.py`."

More than about five lines of prose for one function means you have started writing
the body. Stop, name the error type and the test, move on.

## Rule 2: an executable definition of done

Every plan ships a check script. Not a checklist, not acceptance prose. A file.

Requirements, all of them:

1. **A real file at a stated path**, committed alongside the plan, named in the plan
   frontmatter as `check:`.
2. **Exit 0 from the no-argument run means done. Anything else means not done.** No
   acceptance criterion may exist that the script does not test. A criterion that
   cannot be scripted is converted into one that can, or moved to the reviewer
   checklist.
3. **One command from a clean checkout, no manual steps.** If the checks need an
   environment (a virtualenv, a dependency), the script builds it, quietly, with its
   output in a log file. The repo has its own test-runner config (for pytest, a
   `pytest.ini` or `[tool.pytest]` at the root) and the script cuts discovery at the
   root (`--confcutdir=.`): otherwise pytest can adopt a parent directory's config
   and `conftest.py`. An optional task argument (`check.sh T3`) narrows the run to
   one task's checks so the implementer can go green task by task; a narrowed run
   prints that it is partial, and is never "done".
4. **Written before implementation, and red at that moment.** Run it on the
   unimplemented tree and paste the raw output into the plan. Every check for new
   behaviour fails for its own reason: an assertion, or an ImportError or
   AttributeError naming a module or symbol the plan says to create. A missing
   dependency or tool, a wrong path, or pytest exit 4 (file not found) or 5 (no
   tests collected) is a setup error, not a red check. Checks that guard existing
   behaviour pass. A check script that passes before any code exists tests nothing.
5. **One named check per acceptance item**, each able to fail on its own: one test
   runner call per check, so a collection error in one file cannot hide the others.
6. **Short output.** The implementer reads it into its context: one line per check
   plus only the failing detail (for pytest, `-q --tb=line --show-capture=no`). A red
   run that prints a traceback per test can fill a 32K window on its own.
7. **Read-only to the implementer.** The plan lists every file the implementer may
   create or change, and tells it: never edit or add anything else, above all the
   check script, the acceptance tests, the test-runner config, or a `conftest.py`.
   If a check looks wrong or impossible to satisfy, stop and report the check name,
   its output, and why. Do not work around it.

The implementer reports each round with the raw output of the no-argument run, in
its report message, never in the plan file. That output is progress, not the
verdict: a weak model will report runs it never made. Done is decided by the
reviewer's own run (Review, below). A weak model can talk its way past a prose
criterion; it cannot talk a non-zero exit code into a zero when it is not the one
running the check.

Shape:

```bash
#!/usr/bin/env bash
# Definition of done: exit 0 means done. Run it with no arguments.
# A task id (T1..Tn) narrows the run to that task: a partial run, never "done".
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)" || exit 2
unset PYTEST_ADDOPTS PYTEST_PLUGINS
only=${1:-}
fail=0 ran=0
check() {
  local task=$1 name=$2; shift 2
  [ -n "$only" ] && [ "$only" != "$task" ] && return 0
  ran=$((ran + 1)); echo "== $task $name"
  [ $# -gt 0 ] || { echo "FAIL: $task $name: no command"; fail=1; return 0; }
  "$@" || { echo "FAIL: $task $name"; fail=1; }
}
# expect_exit CODE TEXT CMD...: exactly exit CODE, with TEXT in stderr
expect_exit() {
  local want=$1 text=$2 err got; shift 2
  err=$("$@" 2>&1 >/dev/null); got=$?
  [ "$got" -eq "$want" ] && [[ $err == *"$text"* ]] || { echo "  exit $got: ${err:0:200}"; return 1; }
}
# all_pass N ARGS...: exactly N tests ran and passed; none skipped, failed or
# errored. Counted from pytest's junit report: summary text can be quietened away.
all_pass() {
  local want=$1 xml; shift; xml=$(mktemp)
  python3 -m pytest -q --tb=line --show-capture=no --confcutdir=. --junitxml="$xml" "$@"
  python3 - "$xml" "$want" <<'PY'
import sys, xml.etree.ElementTree as ET
try:
    root = ET.parse(sys.argv[1]).getroot()
except Exception as e:
    sys.exit(f"  no test report: {e}")
s = root if root.tag == "testsuite" else root.find("testsuite")
n = {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
passed = n["tests"] - n["failures"] - n["errors"] - n["skipped"]
if passed != int(sys.argv[2]) or n["failures"] or n["errors"] or n["skipped"]:
    sys.exit(f"  {passed} passed, expected {sys.argv[2]}: {n}")
PY
}

check T1 "window parser unit tests"      all_pass 6 tests/acceptance/test_window.py
check T2 "CLI rejects a bad date range"  expect_exit 2 "invalid date" ./mytool --from 2026-13-01 data.csv

[ "$ran" -gt 0 ] || { echo "FAIL: no check matches '$only'"; exit 2; }
[ -n "$only" ] && echo "PARTIAL RUN ($only only): not the definition of done"
exit $fail
```

Verified under bash 3.2 and 5: every check runs even after one fails, and the
failures are named. T2 is red when the tool is missing and when it rejects `--from`
as an unknown option, and green only for exit 2 with the message. T1 is red when a
test fails, when a hook skips or deselects tests (also with `addopts = -q` in the
config, which hides pytest's summary line), when fewer or more than 6 tests pass,
when the test file is missing, and when production code exits the process on
import (`sys.exit` or `os._exit`: a collection error, or no report at all). A
check with no command fails, an unknown task id fails, and `T1` alone prints the
partial-run line.

- `set -uo pipefail` without `-e`: every check runs, so one round shows every failure.
- Assert the exact exit code and the message, never a bare negation: `! ./mytool
  --from bad` is green when the tool is missing, crashes, or rejects the flag
  because the feature does not exist yet.
- A skipped test is not a passing one: a `conftest.py` hook can mark every test
  skipped, or deselect it, and pytest still exits 0. Count passes from a structured
  report against the number of acceptance tests you wrote, never from summary text.
- Never pipe a check call or a command inside one. `check ... | tail` runs `check`
  in a subshell and loses `fail=1`, and a pipe inside `bash -c` does not inherit
  `pipefail`. Shorten output with the tool's own flags instead.

### Prove the check without implementing the feature

Do not build a working implementation to show the check can pass: not in a scratch
clone, not as a spike, not as a replay of your own plan. That implementation is
written on the expensive model, which is the cost this skill exists to avoid, and
once it exists its code leaks into the plan.

Prove the check with these instead:

- The red run from requirement 4: every new-behaviour check fails for its own reason.
- For each check, name the wrong-but-plausible implementation it is there to catch
  (unsorted input, an off-by-one at a boundary, a parser that accepts `20260105`) and
  confirm by reading that some check fails on it. Add a check where none does.
- A check you cannot convince yourself is satisfiable points at a contract defect.
  Fix the contract in the plan.

| Thought | Reality |
|---|---|
| "I need to prove the check can pass" | The contract shows it can be satisfied; the red run shows it tests something. Making it pass is the implementer's job. |
| "It's a throwaway, outside the repo" | Deleting it does not refund the tokens. |
| "A reviewer asked which wrong versions slip through" | Answer by reading the checks against the contract, and add the missing check. |
| "The plan is more reliable if I paste working code" | Then the weak model is a typist, and there was no reason to delegate. |

If the implementer later reports a check it cannot satisfy (requirement 7), fixing
it is a planner commit and a new pin (Rule 3), never an edit by the implementer.

Anti-patterns that void the rule:

- A trailing `exit 0`, or a script whose last command always succeeds.
- Checks that grep for a string the implementer can add without implementing anything.
- "Run the test suite" with no assertion that the new test actually exists.
- Accepting the implementer's pasted output as the verdict.

## Rule 3: pin the approved spec

During implementation the plan file gets edited. "Clarified the spec to match what
we built" is a normal, well-intentioned commit. Once it lands, the working copy is a
record of the implementer's assumptions and still reads exactly like a spec. Review
a diff against it and the spec-drift defect class, code that is clean, correct, and
implements something other than what was agreed, becomes invisible.

Pin after the user approves the plan in writing-plans' review step. If the review
changes the plan, commit the change and pin again. `code_baseline` marks the last
commit before implementation: it moves with a re-pin only while no implementation
commit exists, and never after. A later re-pin, such as a check correction, updates
`spec_pinned_at` and the handoff record only, so the review diff still starts
before the first implementation commit. In whichever repo holds the plan:

1. Set `status: approved` and `approved:` in the frontmatter, and commit the plan
   with its check script, acceptance tests and red output.
2. `git rev-parse HEAD`. That is the approved spec revision.
3. Write it into the frontmatter as `spec_pinned_at:`, and set `code_baseline:` in
   the same commit:
   - **Plan in the same repo as the code:** the same SHA as `spec_pinned_at`. It is
     already known when you write the pin line, and nothing but the pin line sits
     between it and the first implementation commit.
   - **Plan in a separate repo:** the code repo's HEAD before any implementation
     commit.
4. Write the handoff record, outside the implementer's reach (the ticket, or the
   message that hands the plan over): both SHAs, `checks_at` (below), the check
   command, the file list and read-only rule from Rule 2.7, and, for whoever drives
   the implementer, a fresh session per subtask (Rule 4). The frontmatter copy is
   inside the implementer's reach: a model that "clarifies" the plan can just as
   helpfully "update" `spec_pinned_at` to match.

`checks_at` is the commit in the code repo that holds the approved check script and
acceptance tests: `spec_pinned_at` when plan and code share a repo; otherwise the
code-repo commit where you added them, before implementation. A check correction
later is a new planner commit, and the handoff record names it as the new
`checks_at`.

If the plan points at a separate spec file in the same repo, the pin covers it too.

The recorded SHA is deliberately one commit behind the file you are reading. It names
the tree where the plan body was the approved body, before the pin line existed.
That is correct, not an off-by-one.

Why it must be recorded at approval and cannot be reconstructed: git keeps every
revision, but nothing in git records which revision was *agreed*. A week later the
file's log is a dozen commits with messages like "update plan", and the approval is
not distinguishable from the drift.

## Review: someone other than the implementer declares done

With the SHAs from the handoff record, never from the working copy, in the code
repo:

1. **Integrity.** `git diff --exit-code <checks_at> HEAD -- <check script>
   <acceptance tests> <test-runner config>` prints nothing. Any change there voids
   the result: the implementer edited what defines done.
2. **Scope.** `git diff --name-only <code_baseline> HEAD` lists only the files the
   plan lets the implementer change, the plan itself, and the files in step 1.
   Anything else added or changed voids the result, whatever it is: a
   `conftest.py`, a runner config, a `sitecustomize.py` or `.pth` file can change
   what the check executes without touching the check.
3. **The run.** In a fresh clone of the implementer's HEAD, not its working tree,
   run the check with no arguments. Exit 0 is done. Anything else is not done,
   whatever the implementer reported. The fresh clone also catches work that
   exists only uncommitted on the implementer's machine.
4. Read the spec with `git -C <plan repo> show <spec_pinned_at>:<path/to/plan.md>`
   (and the spec file, if there is one), never the working copy.
5. Review `git diff <code_baseline>..HEAD`: the implementation, plus any edit to the
   plan made after approval, which is exactly the drift to look for. Then walk the
   reviewer checklist.

## Rule 4: decompose until a wrong result is obvious at a glance

Size a subtask so that a wrong result is visible without re-deriving the design: one
named behaviour change, its test, its check. If judging correctness requires holding
three files in your head at once, split it.

How many files one subtask may touch depends on the implementer's coherence limit,
which is per model, quantization and context cap:

- A measured value exists for this exact configuration: size to it. Find it with
  `grep -rn '^max_files:' docs/` and use only lines marked as measured for the same
  model, quantization and context cap.
- Otherwise: one production file plus its test per subtask, recorded as
  `max_files: 1  # default, unmeasured`.

Do not measure while writing a plan. Measuring is a separate one-off job:
[measuring-implementer-coherence.md](measuring-implementer-coherence.md).

Put in the handoff record, for whoever drives the implementer: a fresh session per
subtask, and re-read the plan off disk at the start of each. Long sessions compact,
and after compaction the agent works from a summary of the spec rather than the
spec itself. No error message, just drift.

## Frontmatter template

```yaml
---
status: approved
approved: 2026-09-22
spec_pinned_at: 74fc6b95e0960057cf4b5b662247eee553624b22  # plan repo HEAD at approval
code_baseline: 74fc6b95e0960057cf4b5b662247eee553624b22   # same repo: = spec_pinned_at
implementer: qwen3-coder-30b-a3b Q4_K_M, 32K context      # model, quantization (n/a if hosted), context cap
max_files: 1                                              # default, unmeasured (Rule 4)
check: scripts/check-<slug>.sh                            # no-argument exit 0 means done
---
```

## Pitfalls

- Applying these rules when the gate said stop, because they looked cheap.
- Building a reference implementation "to prove the check can pass".
- A check that passes before implementation, or whose new-behaviour checks fail on
  a setup error instead of the missing behaviour.
- A negated check (`! cmd`), or a piped check call.
- A check that needs a manual setup step on a clean checkout.
- Leaving the check, the acceptance tests or the test config editable by the
  implementer, or giving it no way to report a check it cannot satisfy.
- Counting skipped tests as passing, or a check call with no command.
- Moving `code_baseline` after implementation started, which hides the work
  before it from the review diff.
- Accepting the implementer's pasted run as the verdict instead of running the
  pinned check yourself in a fresh clone, after the integrity and scope diffs.
- Reviewing against the working copy of the spec, or taking the pin from it.
- Sizing subtasks by token count instead of the coherence limit.
- Writing the body on the expensive model because the contract felt
  underspecified. Add the error type and the test instead.

## Verification

Before handing the plan over:

- [ ] `implementer:` is recorded, and the gate's answer was known before drafting.
- [ ] No production function bodies; every function is named with a full signature and an error type.
- [ ] No reference implementation was built.
- [ ] The check script is committed, runs from a clean checkout with no manual steps, and its red output is pasted into the plan.
- [ ] Every new-behaviour check fails in that red run for its own reason; no negated or piped checks.
- [ ] Every acceptance item maps to a separately failing named check; unscriptable constraints are on the reviewer checklist.
- [ ] Check output is one line per check plus failing detail.
- [ ] The plan lists every file the implementer may change, says everything else is read-only, and says to stop and report a check it cannot satisfy.
- [ ] The plan was pinned after the user approved it; `git show <spec_pinned_at>:<path>` returns the plan body.
- [ ] The handoff record carries both SHAs, `checks_at`, the check command, the file list, and the fresh-session instruction.
- [ ] Each subtask touches one production file plus its test, or cites a measured `max_files`.
