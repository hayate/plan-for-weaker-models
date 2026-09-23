# Evals for plan-for-weaker-models

Pressure scenarios for editing this skill test-first (superpowers:writing-skills):
run them without the change to see the failure, make the change, run them again.
Score what the run left on disk with `score.sh`, never the agent's own report.

## Setup, per run

1. Copy `fixture-ledger/` to a scratch directory, `git init`, commit it on `main`.
   Every run gets its own copy and its own empty scratch root.
2. Freeze the skill under test: copy SKILL.md and the files it links to a directory
   of their own. Never point a run at the working copy you are editing.
3. Dispatch one fresh subagent with the prompt from `prompts/`, replacing `<REPO>`,
   `<SKILL>` (the frozen SKILL.md) and `<SCRATCH>` (the run's scratch root).
4. W and SD only: when the agent reports the plan ready, send a second turn,
   "Approved.", and save that reply. The skill pins after approval, so the pin is
   scored after this turn.
5. Save the agent's final reply as text, and score:
   `bash score.sh <U|S|W> <run repo> [scratch root] [reply file]`.
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

Not covered yet, each needing a scenario of its own: a plan in a separate repo from
the code, a measured `max_files` to reuse or reject, a peer-model implementer, and
an implementation stage that hands the pinned plan to a weak implementer and scores
its result against hidden black-box tests. That last one is the only test of the
skill's central claim, that a weak model delivers from these plans.

## Results, 2026-09-23

Planner: Claude Opus 5.5 subagents, with Andrea's global CLAUDE.md in force (TDD, a
Codex review of every plan, which makes each run 15-25 minutes). n is 2 or 3 per
cell, so read these as directional. Runs predate `score.sh` and the `<SCRATCH>`
line: they were scored by hand from the repos, with the same checks `score.sh` now
makes, and `score.sh` was validated against 11 of them (all 11 scored as by hand).

Skill versions: v0 is d19073e. v1 is 059dadf without its Rule 3 handoff step (added
after these runs from their own findings). The current split into SKILL.md and
rules-for-weak-implementers.md has not been run yet.

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
