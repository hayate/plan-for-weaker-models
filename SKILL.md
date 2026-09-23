---
name: plan-for-weaker-models
description: "Use when writing an implementation plan, before drafting it, and whenever it is unclear who will implement it; also when re-sizing a plan after a weaker implementer reported done and was not. Applies when a weaker model than the planner implements: a local or quantized model, a cheaper model behind a coding CLI, subagents on a smaller model."
author: hayate
license: MIT
---

# Plans for weaker models

A strong model fills a gap in a spec by inferring intent from the surrounding code.
A weak model fills it with the most common pattern in its training data, then
reports success. When a weak model implements, the plan is the only place those
gaps can be closed, so it carries load that a same-model plan does not. That load
is real work, and it is wasted when the implementer is as strong as the planner.

## Gate: who implements this plan?

Settle this before drafting anything.

| Implementer | Do this |
|---|---|
| You, in this session (writing-plans' Native execution) | Stop. This skill does not apply. |
| Your own model or one at least as strong, in any session; or a human | Stop. These rules target how weaker models fail. |
| Subagents you dispatch per task (writing-plans' Subagent-driven execution) | Apply, unless every implementer subagent will run on your model. subagent-driven-development picks a cheap model for small, fully specified tasks, which is what this skill produces. |
| A weaker model: local, quantized, smaller or cheaper | Apply. |
| Nothing to implement (research notes, no acceptance surface) | Stop. |
| Not stated, not decided, or you cannot tell whether it is weaker | Ask the user now, then wait. |

The question, in one message: "Who will implement this plan: me in this session,
subagents I dispatch per task (they may run on cheaper models), or another model?
If another model, which one, at what quantization and context size?" The answer
also settles writing-plans' execution method, so do not ask it again at the end.

Ask before drafting. Do not draft the plan and ask at the end, and do not assume a
weak implementer to be safe: a weak-model plan costs far more to write, and for a
strong implementer that cost buys nothing. When the gate says stop, "a couple of
these rules are cheap, I'll apply them anyway" is the reasoning the gate exists to
stop. Plan as you normally would.

## When the gate says apply

**REQUIRED:** read [rules-for-weak-implementers.md](rules-for-weak-implementers.md)
in full before drafting. It lists where it overrides writing-plans, and holds the
four rules (contracts not bodies, an executable definition of done, a pinned spec,
subtasks sized to the implementer), the review procedure, the frontmatter template
and the verification checklist.
