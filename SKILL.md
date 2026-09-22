---
name: plan-for-weaker-models
description: "Write plans a weak model can execute without drifting."
version: 0.1.0
author: hayate
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [planning, delegation, weak-models, acceptance, spec]
    related_skills: [plan, test-driven-development]
---

# Plans for weaker models

Use when a plan written on a strong model will be implemented by a weaker one: a
frontier model driving a cheaper one through a coding CLI, a local model, any
small or heavily quantized implementer. A strong model fills a gap in the spec
by inferring intent from the surrounding code. A weak model fills it with the
most common pattern in its training data, then reports success. The plan is the
only place those gaps can be closed, so it carries load that a same-model plan
does not.

## When to use

- Writing a spec or plan that a different, weaker model will implement.
- Handing work to a local model, or to any harness whose reviewer is not the writer.
- Re-sizing an existing plan after a weak implementer declared something done that was not.

Don't use for: plans you will implement yourself in the same session on the same
model, or research notes with no acceptance surface.

## Rule 1: name the contract, not the body

The plan fixes anchors. It does not write code.

Name: file path, function or class name, full signature with types, the error
type raised, the constant and where it lives, the call sites that change, the
test file.

Do not write: the function body, the algorithm, the loop, the query.

Discriminator for any line you are about to add: if removing it would still let
the implementer produce a wrong-but-plausible *interface*, keep it. If removing
it only rules out one of several correct ways to satisfy a contract you already
named, cut it.

- Too vague: "handle errors appropriately". That is an empty slot, and the weak
  model fills it with a bare except that logs and continues.
- Too far: ten lines of pseudocode for the body. You are now implementing on the
  expensive model and paying for it twice.
- Right: "`parse_window(raw: str) -> tuple[date, date]` in `lib/window.py`,
  raises `ValueError` on unparseable input. Both existing call sites already
  catch `ValueError`; do not swallow it inside the helper. Tests go in
  `tests/test_window.py`."

More than about five lines of prose for one function means you have started
writing the body. Stop, name the error type and the test, move on.

## Rule 2: an executable definition of done

This is the rule the skill exists for. Every plan ships a check script. Not a
checklist, not acceptance prose. A file.

Requirements, all of them:

1. **A real file at a stated path**, committed alongside the plan, named in the
   plan frontmatter as `check:`.
2. **Exit 0 means done. Any non-zero means not done.** No prose acceptance
   criterion may exist in the plan that the script does not also test. If it
   cannot be scripted, either cut it or convert it into something that can.
3. **One command, clean checkout, no arguments, no manual steps.** A check that
   needs a human to interpret it is a prose criterion wearing a shell.
4. **Written before implementation starts, and it must fail at that moment.**
   Run it against the unimplemented tree and paste the non-zero output into the
   plan. A check script that passes before any code exists tests nothing, and
   that failure survives every later review because everything is green.
5. **One named check per acceptance item**, each able to fail on its own. A
   single monolithic pass/fail hides which item regressed.
6. **Raw pasted output every round**, including after each fix round. A fix
   round without a green script is not a fix round.

Why this rule carries the others: a weak model will talk its way past a prose
criterion, will report that tests pass without having run them, and will declare
a project done. It cannot talk a non-zero exit code into a zero.

Shape:

```bash
#!/usr/bin/env bash
set -uo pipefail
fail=0
check() { local name=$1; shift; echo "== $name"; "$@" || { echo "FAIL: $name"; fail=1; }; }

check "window parser unit tests"      pytest -q tests/test_window.py
check "CLI rejects a bad date range"  bash -c '! ./mytool --from 2026-13-01'
check "no new bare excepts"           python scripts/lint_excepts.py src/

exit $fail
```

Note `set -uo pipefail` without `-e`: every check must run so you see all
failures in one round, not just the first. Verified: with a passing, a failing
and a third check, all three run, the failure is named, and the script exits 1.

Anti-patterns that void the rule:

- A trailing `exit 0`, or a script whose last command always succeeds.
- Checks that grep for a string the implementer can add without implementing anything.
- "Run the test suite" with no assertion that the new test actually exists.
- Accepting the implementer's summary of the run instead of the pasted output.

## Rule 3: pin the approved spec

**Frontmatter** is the `---` delimited YAML block at the top of a markdown file.
It holds metadata about the document and is not part of the prose.

The problem it solves: during implementation the plan file gets edited.
"Clarified the spec to match what we built" is a normal, well-intentioned
commit. Once it lands, the working copy is a record of the implementer's
assumptions and still reads exactly like a spec. Review a diff against it and
the spec-drift defect class, code that is clean, correct, and implements
something other than what was agreed, becomes invisible.

Procedure at approval time, in whichever repo holds the plan:

1. Commit the finished plan.
2. `git rev-parse HEAD`. That is the approved spec revision.
3. Write it into the plan frontmatter as `spec_pinned_at:` and commit that
   one-line change.
4. Record the implementation repo's HEAD before any implementation commit as
   `code_baseline:`. The review diff is then `git diff <code_baseline>..HEAD`,
   exactly the implementation work and nothing else.

Reviewers read the spec with:

```bash
git show <spec_pinned_at>:<path/to/plan.md>
```

never the working copy. When plan and code live in separate repos, add
`-C <plan repo>`.

The recorded SHA is deliberately one commit behind the file you are reading. It
names the tree where the plan body was the approved body, before the pin line
existed. That is correct, not an off-by-one.

Why it must be recorded at approval and cannot be reconstructed: git keeps every
revision, but nothing in git records which revision was *agreed*. A week later
the file's log is a dozen commits with messages like "update plan", and the
approval is not distinguishable from the drift. Verified with three commits
(draft, pin, drift): `git show <sha>:<path>` returns the approved body while the
working copy shows the drifted one, and `git log -- <path>` gives no way to tell
which commit was the approval.

A tag (`git tag spec/<slug>-approved`) works as well and is easier to type.
Frontmatter travels with the file into any copy of it; a tag does not. Use
frontmatter as the record and add a tag if you like typing names.

## Rule 4: decompose until a wrong result is obvious at a glance

Size a subtask so that a wrong result is visible without re-deriving the design:
one named behaviour change, its test, its check. If judging correctness requires
holding three files in your head at once, split it.

Coherence limits are per implementer, and per build for a local model. A
frontier model holds a ten-file refactor. A strong non-frontier model degrades
somewhere around three. Do not infer a number from benchmark scores: agentic
coding benchmarks score single self-contained tasks, not multi-file coherence,
and locally the variables that actually move are quantization and the context
cap you accepted to fit the weights. A Q6 build capped at 128K and a Q4 build
capped at 32K are two different implementers with one model name.

Measure it once per model/quant/context configuration, about thirty minutes:

1. Take a real completed multi-file task from the repo's history.
2. Give the model the approved spec scoped to N files and run it.
3. Score by check script, and separately by whether the last file it touched is
   still consistent with the first.
4. Halve N on failure. Stop at the largest N that passes twice.

Record the result as `implementer:` and `max_files:` in the plan frontmatter so
the next plan is sized from a measurement rather than a guess.

Default until measured: one file of production change plus its test per subtask,
a new session per subtask, and re-read the plan off disk at the start of each
one. Long sessions compact, and compaction is usually done by the harness's
cheap model, so the agent's memory of the spec silently becomes a small model's
summary of it. No error message, just drift.

## Frontmatter template

```yaml
---
status: approved
approved: 2026-09-22
spec_pinned_at: 74fc6b95e0960057cf4b5b662247eee553624b22  # plan repo HEAD at approval
code_baseline: a0b71a0d2ff31c0e9d3a7e4b5c6d7e8f90a1b2c3   # impl repo HEAD before work starts
implementer: <model that will write the code>
max_files: 3                                              # measured, see Rule 4
check: scripts/check-<slug>.sh                            # exit 0 means done
---
```

## Pitfalls

- A check script that passes before implementation. Run it at write time and
  confirm it fails.
- Prose acceptance criteria the script does not cover. Encode or delete them.
- Reviewing against the working copy of the spec instead of the pinned revision.
- Sizing subtasks by token count. The limit is coherence, not context length: a
  model with 128K context can still lose the thread at file four.
- Letting the model that wrote the code decide it is done. Self-review by a weak
  model re-reads its own reasoning and finds it convincing.
- Writing the body on the expensive model because the contract felt
  underspecified. Add the error type and the test instead.

## Verification

Before handing the plan to the implementer:

- [ ] Check script exists, is committed, and has failed once with output pasted into the plan.
- [ ] Every acceptance item maps to a separately failing named check.
- [ ] No prose criterion exists without a corresponding check.
- [ ] `git show <spec_pinned_at>:<path>` returns the plan body.
- [ ] `code_baseline` recorded before the first implementation commit.
- [ ] Each subtask names one file of production change plus its test, or cites a measured `max_files`.
- [ ] Every function named with a full signature and an error type, and no function has a written body.
