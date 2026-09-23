# Evals for plan-for-weaker-models

Pressure scenarios for editing this skill test-first (superpowers:writing-skills):
run them without the change to see the failure, make the change, run them again.
Score what the run left on disk with `score.sh`, never the agent's own report.

## Setup, per run

1. Copy `fixture-ledger/` to a scratch directory, `git init`, commit it on `main`,
   and record that commit's SHA as the run's base. Every run gets its own copy and
   its own empty scratch root.
2. Freeze the skill under test: copy SKILL.md and the files it links to a directory
   of their own. Never point a run at the working copy you are editing.
3. Dispatch one fresh subagent with the prompt from `prompts/`, replacing `<REPO>`,
   `<SKILL>` (the frozen SKILL.md) and `<SCRATCH>` (the run's scratch root).
4. W and SD only: when the agent reports the plan ready, send a second turn,
   "Approved.", and save that reply. The skill pins after approval, so the pin is
   scored after this turn. The prompt says the orchestrator relays Andrea's
   approval: without that line, a careful planner rightly refuses to treat an
   agent's "Approved." as the user's consent (one 2026-09-23 run did).
5. Save the agent's final reply as text, and score:
   `bash score.sh <U|S|W> <run repo> <base sha> [scratch root] [reply file]`.
   Read every LOOK line. SD is scored with W.

The host must not have pytest importable from its default `python3`; `score.sh`
warns when it does, because a check that never builds its own environment would
then pass the fresh-clone criterion.

## Scenarios

| Prompt | Situation | Scored as | Pass |
|---|---|---|---|
| `U.txt` | implementer not stated | U | Asks who implements; no commit, no uncommitted files. |
| `U-noinvite.txt` | as U, but the prompt does not invite questions | U | As U. Tests the gate itself rather than the prompt's escape hatch. |
| `S.txt` | the planner implements the plan itself | S | Plan added with code blocks; no pin, `max_files` or `check:` fields; no check script. |
| `W.txt` | a local Q4 model implements | W | See below. |
| `SD.txt` | subagent-driven execution | W | The gate applies (subagents may be cheap models), then as W. |
| `control.txt` | W without the skill | W | Expected to fail: the baseline. |

W passes when:
- `implementer:` is recorded, and no function in the plan has a production body.
- Nothing differing from the fixture's `ledger/*.py` exists in the scratch root (no
  reference implementation), and no production code is committed.
- The check, run from a fresh clone of HEAD, is red, with no setup error and with
  named FAIL lines; its output fits in 16 KB.
- New-behaviour checks fail for their own reason: an assertion, or an ImportError
  or AttributeError naming a symbol the plan creates. A missing tool or dependency,
  a wrong path, or pytest exit 4 or 5 is a setup error.
- `spec_pinned_at` resolves, `code_baseline` equals it, only the plan changed after
  it, and the reply to "Approved." carries the SHA.
- The plan tells the implementer what is read-only.

`score.sh` covers each line mechanically except "own reason", which shows in the
saved red run, and production bodies, which it flags as LOOK for a human read.

## Stage E: does a weak implementer deliver from the plan?

The scenarios above score the plan. Stage E scores the skill's central claim: a
weaker model, working only from the pinned plan, delivers correct code.

1. Take a W or SD run that passed, after "Approved.", and clone its repo.
2. For each task in order, start a fresh session on the weaker model (a Claude
   Haiku 4.5 subagent stands in for a local model) with only: the plan path, the
   handoff record (SHAs, `checks_at`, check command, file list, read-only rule), and
   "Implement task Tn: re-read the plan from disk, run the check for Tn, commit, and
   report the raw no-argument run."
3. Review as the Review section of rules-for-weak-implementers.md says: the
   integrity diff against `checks_at` is empty, the scope diff from `code_baseline`
   lists only allowed files, and the check run with no arguments in a fresh clone of
   HEAD exits 0.
4. Run the hidden tests, which the implementer never saw:
   `LEDGER_REPO=<fresh clone> python -m pytest -q --confcutdir=evals/hidden evals/hidden`.
   They drive only the CLI surface FEATURE.md defines. Validated: on the
   unimplemented fixture only the 2 existing-behaviour tests pass (9 fail); a
   correct implementation passes all 11; an exclusive `--to`, a month key without
   the year, and `--by-month` ignoring the window each fail at least one.

Record per task whether the implementer stopped and reported a check it could not
satisfy, and whether it touched a read-only file.

Not covered yet, each needing a scenario of its own: a plan in a separate repo from
the code, a measured `max_files` to reuse or reject, and a peer-model implementer.

## Results, 2026-09-23

Planner: Claude Opus 5.5 subagents, with Andrea's global CLAUDE.md in force (TDD, a
Codex review of every plan, which makes each run 15-25 minutes). n is 2 or 3 per
cell, so read these as directional. Runs predate `score.sh` and the `<SCRATCH>`
line: they were scored by hand from the repos, with the same checks `score.sh` now
makes, and `score.sh` was validated against 11 of them (all 11 scored as by hand),
plus three regression repos: a plan committed on `main`, quoted YAML values, and an
`implementer:` that appears only inside a code fence (must fail).

Skill versions: v0 is d19073e. v1 is 059dadf without its Rule 3 handoff step (added
after these runs from their own findings). v2 is 91d7671, the split into SKILL.md
and rules-for-weak-implementers.md, scored with `score.sh`; its sheets are in
`results/2026-09-23/`. Later commits changed the example check's `all_pass` to a
junit count, one gate-row sentence, and the prompts, none of it re-run.

| | Control (no skill), 3 runs | v0 | v1 |
|---|---|---|---|
| U: asks before drafting | - | 0/2 | 2/2 |
| S: skips the skill | - | 0/2 (applied Rules 2-3 anyway) | 2/2 |
| W: no function bodies | 0/3 | 3/3 | 3/3 |
| W: no reference implementation | 0/3 | 0/3 | 3/3 |
| W: check red from a fresh clone, no setup error | 0/3 (1 had no check, 2 needed a manual venv) | 3/3 (B1, B3 need uv) | 3/3 |
| W: `code_baseline` is a SHA equal to `spec_pinned_at` | 0/3 (no pin) | 2/3 (B1 used a tag) | 3/3 |

The fresh-clone row separates skill from no skill, not v1 from v0: v0 runs already
built their own environments.

v2 runs (one each unless noted):

| Scenario | Result |
|---|---|
| U (2 runs: U.txt, U-noinvite.txt) | 2/2 asked who implements and drafted nothing, including the run whose prompt did not invite questions. |
| S | Pass: skipped the skill, planned with writing-plans. It still asked the execution-method question, which the gate answer settles; SKILL.md now says so outside the question paragraph. |
| W (2 runs) | W2: 13/13 after "Approved.". W1: all criteria but the pin: it refused to treat the orchestrator's "Approved." as Andrea's consent (correct), so prompts now say approval is relayed. |
| SD | All criteria but the pin; not sent "Approved." for the same reason. It applied the rules on the subagent-driven row. |

Stage E on W2's pinned plan, Claude Haiku 4.5 implementing, one fresh session per
task: all five tasks committed, T1-T4 green on the first attempt, no read-only file
touched. Review: integrity and scope clean, the no-argument check from a fresh clone
exits 0 (24 checks), and the hidden black-box tests pass 11/11. One slip: task T5
had no check by design (the reviewer reads the README), the prompt told the
implementer to run `check T5` anyway, which exits 2 ("no check matches"), and the
implementer reported "all checks pass" without mentioning it. The prompt now covers
tasks without a check. Done was decided by the reviewer's own run, as designed.

2026-09-24: after Andrea approved W1's and SD1's plans (relayed, his words quoted),
Haiku 4.5 implemented both the same way. Stage E is now 3/3:

| Plan | Tasks | First-attempt green | Read-only touched | Fresh-clone check | Hidden tests |
|---|---|---|---|---|---|
| W2 | 5 | 4/4 checked tasks (T5 has no check) | no | exit 0, 24 checks | 11/11 |
| W1 | 6 | 6/6 | no | exit 0, 29 checks | 11/11 |
| SD1 | 3 | 3/3 | no | exit 0, 10 checks | 11/11 |

Haiku is a stand-in for a local quantized model; how the two compare is not
measured here. A run with a local model through opencode is the next test.
