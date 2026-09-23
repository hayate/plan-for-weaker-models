---
name: plan-for-weaker-models
description: "Use when writing an implementation plan or spec, before drafting it, and whenever it is unclear who will implement it. Applies when a weaker model than the planner implements: a local or quantized model, a cheaper model behind a coding CLI, a subagent on a smaller model."
author: hayate
license: MIT
---

# Plans for weaker models

A strong model fills a gap in a spec by inferring intent from the surrounding code.
A weak model fills it with the most common pattern in its training data, then
reports success. When a weak model implements, the plan is the only place those
gaps can be closed, so it carries load that a same-model plan does not. This skill
is that extra load. It is wasted work when the planner implements the plan itself.

## Gate: who implements this plan?

Settle this before drafting anything.

| Implementer | Do this |
|---|---|
| You, in this session | Stop. This skill does not apply: no check script, no pin, no sizing from it. Plan as you normally would. |
| Another model at least as strong as you | Stop, as above. |
| A weaker model: local, quantized, smaller or cheaper | Apply everything below. Record the model, quantization and context cap as `implementer:`. |
| Not stated | Ask the user now, in one message: "Who will implement this plan: me, in this session, or another model? If another model, which one, at what quantization and context size?" Wait for the answer. |

When the implementer is not stated, ask first. Do not draft the plan and ask at the
end, and do not assume a weak implementer to be safe: a weak-model plan costs far
more to write, and for a strong implementer that cost buys nothing. When the gate
says stop, "these rules are cheap, I'll apply a couple anyway" is the reasoning the
gate exists to stop.

## Precedence over writing-plans

writing-plans asks for a code block in every code step. When this skill applies it
overrides that one point: the plan names contracts (Rule 1) and contains no
production function bodies. Everything else writing-plans asks for still applies:
task structure, exact paths, exact commands. The check script and any acceptance
tests it runs are the definition of done, not the implementation, so write those in
full.

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
  `ValueError`; do not swallow it inside the helper. Tests go in
  `tests/test_window.py`."

More than about five lines of prose for one function means you have started writing
the body. Stop, name the error type and the test, move on.

## Rule 2: an executable definition of done

Every plan ships a check script. Not a checklist, not acceptance prose. A file.

Requirements, all of them:

1. **A real file at a stated path**, committed alongside the plan, named in the plan
   frontmatter as `check:`.
2. **Exit 0 means done. Any non-zero means not done.** No prose acceptance criterion
   may exist in the plan that the script does not also test. If it cannot be
   scripted, cut it or convert it into something that can.
3. **One command from a clean checkout, no manual steps.** If the checks need an
   environment (a virtualenv, a dependency), the script builds it; a script that
   stops with "create the venv first" has a manual step. The full run takes no
   arguments. An optional task argument (`check.sh T3`) may narrow it to one task's
   checks, so the implementer can go green task by task while later tasks still fail.
4. **Written before implementation, and red at that moment.** Run it on the
   unimplemented tree and paste the raw output into the plan. Every check for new
   behaviour fails, and fails for its own reason: its output names the missing
   behaviour, not a setup error. Checks that guard existing behaviour pass. A check
   script that passes before any code exists tests nothing, and that failure
   survives every later review because everything is green.
5. **One named check per acceptance item**, each able to fail on its own. A single
   monolithic pass/fail hides which item regressed.
6. **Short output.** The implementer reads it into its context. Print one line per
   check plus only the failing detail (for pytest, `-q --tb=line`). A red run that
   prints a traceback per test can fill a 32K window on its own.
7. **Raw pasted output every round**, including after each fix round. A fix round
   without a green script is not a fix round.

Why this rule carries the others: a weak model will talk its way past a prose
criterion, will report that tests pass without having run them, and will declare a
project done. It cannot talk a non-zero exit code into a zero.

Shape:

```bash
#!/usr/bin/env bash
set -uo pipefail
fail=0
check() { local name=$1; shift; echo "== $name"; "$@" || { echo "FAIL: $name"; fail=1; }; }

check "window parser unit tests"      pytest -q --tb=line tests/test_window.py
check "CLI rejects a bad date range"  bash -c '! ./mytool --from 2026-13-01'
check "no new bare excepts"           python scripts/lint_excepts.py src/

exit $fail
```

Note `set -uo pipefail` without `-e`: every check must run so you see all failures in
one round, not just the first. Verified: with a passing, a failing and a third check,
all three run, the failure is named, and the script exits 1.

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

Anti-patterns that void the rule:

- A trailing `exit 0`, or a script whose last command always succeeds.
- Checks that grep for a string the implementer can add without implementing anything.
- "Run the test suite" with no assertion that the new test actually exists.
- Accepting the implementer's summary of the run instead of the pasted output.

## Rule 3: pin the approved spec

During implementation the plan file gets edited. "Clarified the spec to match what
we built" is a normal, well-intentioned commit. Once it lands, the working copy is a
record of the implementer's assumptions and still reads exactly like a spec. Review
a diff against it and the spec-drift defect class, code that is clean, correct, and
implements something other than what was agreed, becomes invisible.

Procedure at approval time, in whichever repo holds the plan:

1. Commit the finished plan, with its check script and red output.
2. `git rev-parse HEAD`. That is the approved spec revision.
3. Write it into the plan frontmatter as `spec_pinned_at:`, and set `code_baseline:`
   in the same commit:
   - **Plan in the same repo as the code:** the same SHA as `spec_pinned_at`. It is
     already known when you write the pin line, and nothing but the pin line sits
     between it and the first implementation commit.
   - **Plan in a separate repo:** the code repo's HEAD before any implementation
     commit.
4. Put both SHAs in the handoff record too: the ticket, or the message that hands
   the plan over. The frontmatter is inside the implementer's reach, and a model
   that "clarifies" the plan can just as helpfully "update" `spec_pinned_at` to
   match. Reviewers take the SHAs from the handoff record, not the working copy. A
   check script that guards the pin reads it the same way, from an environment
   variable or argument the reviewer supplies, never from the plan file alone.

The review diff is `git diff <code_baseline>..HEAD`: the implementation work, plus
any edit to the plan made after approval, which is exactly the drift a reviewer
should see.

Reviewers read the spec with:

```bash
git show <spec_pinned_at>:<path/to/plan.md>
```

never the working copy. When plan and code live in separate repos, add
`-C <plan repo>`.

The recorded SHA is deliberately one commit behind the file you are reading. It names
the tree where the plan body was the approved body, before the pin line existed.
That is correct, not an off-by-one.

Why it must be recorded at approval and cannot be reconstructed: git keeps every
revision, but nothing in git records which revision was *agreed*. A week later the
file's log is a dozen commits with messages like "update plan", and the approval is
not distinguishable from the drift.

## Rule 4: decompose until a wrong result is obvious at a glance

Size a subtask so that a wrong result is visible without re-deriving the design: one
named behaviour change, its test, its check. If judging correctness requires holding
three files in your head at once, split it.

How many files one subtask may touch depends on the implementer's coherence limit,
which is per model, quantization and context cap:

- A measured `max_files` exists for this exact configuration (from an earlier plan's
  frontmatter): size to it.
- Otherwise: one production file plus its test per subtask, recorded as
  `max_files: 1  # default, unmeasured`.

Do not measure while writing a plan. Measuring is a separate one-off job:
[measuring-implementer-coherence.md](measuring-implementer-coherence.md).

Tell the implementer to start a new session per subtask and re-read the plan off
disk at the start of each one. Long sessions compact, and compaction is usually done
by the harness's cheap model, so the agent's memory of the spec silently becomes a
small model's summary of it. No error message, just drift.

## Frontmatter template

```yaml
---
status: approved
approved: 2026-09-22
spec_pinned_at: 74fc6b95e0960057cf4b5b662247eee553624b22  # plan repo HEAD at approval
code_baseline: 74fc6b95e0960057cf4b5b662247eee553624b22   # same repo: = spec_pinned_at
implementer: qwen3-coder-30b-a3b Q4_K_M, 32K context      # model, quant, context cap
max_files: 1                                              # default, unmeasured (Rule 4)
check: scripts/check-<slug>.sh                            # exit 0 means done
---
```

## Pitfalls

- Drafting the plan, then asking who implements it at the end. Ask first.
- Applying these rules when you are the implementer, because they looked cheap.
- Building a reference implementation "to prove the check can pass".
- A check script that passes before implementation, or whose new-behaviour checks
  fail on a setup error instead of the missing behaviour.
- A check that needs a manual setup step on a clean checkout.
- Prose acceptance criteria the script does not cover. Encode or delete them.
- Reviewing against the working copy of the spec instead of the pinned revision.
- Sizing subtasks by token count instead of the coherence limit.
- Letting the model that wrote the code decide it is done. Self-review by a weak
  model re-reads its own reasoning and finds it convincing.
- Writing the body on the expensive model because the contract felt
  underspecified. Add the error type and the test instead.

## Verification

Before handing the plan to the implementer:

- [ ] The implementer was known before drafting (asked if unstated), and is recorded as `implementer:`.
- [ ] No production function bodies; every function is named with a full signature and an error type.
- [ ] No reference implementation was built.
- [ ] The check script is committed, runs from a clean checkout with no manual steps, and its red output is pasted into the plan.
- [ ] Every new-behaviour check fails in that red run for its own reason.
- [ ] Every acceptance item maps to a separately failing named check, and no prose criterion exists without one.
- [ ] Check output is one line per check plus failing detail.
- [ ] `git show <spec_pinned_at>:<path>` returns the plan body, `code_baseline` is recorded, and both SHAs are in the handoff record.
- [ ] Each subtask touches one production file plus its test, or cites a measured `max_files`.
