# Evals for plan-for-weaker-models

Pressure scenarios for editing this skill test-first (superpowers:writing-skills):
run them without the change to see the failure, make the change, run them again.

## Setup

For each run, copy `fixture-ledger/` to a scratch directory and make it a git repo
(`git init && git add -A && git commit -m fixture`). Every run gets its own copy.
Tests need pytest: `pytest -q` from the fixture root (its `pytest.ini` sets
`pythonpath` and stops conftest discovery at the root).

Dispatch one fresh subagent per run with the matching prompt below. Point `<SKILL>`
at a frozen copy of the SKILL.md under test, not the working copy you are editing.

## Prompts

Shared tail for every prompt:

> Your job right now is the plan only - do not implement the feature. Save the plan
> in that repo (any path you like under docs/), plus any supporting files you think
> the plan needs, and commit them in that repo. If you would need to ask Andrea
> something before you could write a sensible plan, stop and reply with only the
> question(s). Otherwise, when done, reply with: the paths you created, and anything
> you would ask Andrea before handing off.

- **W (weak implementer):** "You are working in the git repo at `<REPO>`. Read
  README.md and FEATURE.md there. Andrea wants that feature built. You are writing
  the implementation plan. The implementation will be done by a different model:
  qwen3-coder-30b-a3b quantized to Q4_K_M, running locally with a 32K context
  window, driven through a coding CLI. You will not see its work until it reports
  done. This skill is loaded in your session: `<SKILL>` - read it. Use whatever
  other skills or process you would normally use as well." + tail
- **S (planner implements):** as W, but replace the implementer sentences with "You
  are writing the implementation plan, and right after it is approved you yourself
  will implement it, in this same session." + tail
- **U (implementer unstated):** "... Andrea wants that feature built, and has asked
  you to write the implementation plan." with the skill line, no implementer. + tail
- **Control:** W without the skill line.

## Pass criteria (score from the repo, not the agent's report)

| Scenario | Pass |
|---|---|
| U | Replies with only the gate question; repo HEAD unchanged. |
| S | Plan exists; no `spec_pinned_at`, `code_baseline`, `max_files`, `check:` or check script. |
| W | No production function bodies in the plan. No reference implementation: no changed `ledger/*.py` in the repo or in any scratch clone the agent made. The check script, run from a fresh clone with no venv, sets up its own environment and exits non-zero with every new-behaviour check failing on missing behaviour. `code_baseline` equals `spec_pinned_at`. |

Agents report what they intended. Score what they left on disk: grep the plan,
diff the scratch clones against the fixture, run the check from a fresh clone.

## Results, 2026-09-23

Planner model: Claude Opus 5.5 subagents, with the global CLAUDE.md in force (TDD,
Codex review of every plan). Runs take 15-25 minutes each because of the Codex step.

| | Control (no skill), 3 runs | v0 (d19073e) | v1 |
|---|---|---|---|
| U: asks before drafting | - | 0/2 | 2/2 |
| S: skips the skill | - | 0/2 (applied Rules 2-3 anyway) | 2/2 |
| W: no function bodies | 0/3 | 3/3 | 3/3 |
| W: no reference implementation | 0/3 | 0/3 | 3/3 |
| W: check runs from a fresh clone | 0/2 (needed a manual venv) | not scored | 3/3 |
| W: same-repo pin without a workaround | 0/3 (no pin) | 2/3 (B1 fell back to a tag) | 3/3 |

Open after v1: the Rule 3 handoff-record step (pin SHAs outside the repo) was added
from the v1 runs' own Codex findings and has not been re-run as a scenario.
