# Measuring an implementer's coherence limit

A one-off calibration job, run once per implementer configuration. It is not part of
writing a plan: a plan uses the result (`max_files:`) or the default, never a
measurement taken on the spot.

## Why measure

Coherence limits are per implementer, and per build for a local model. A frontier
model holds a ten-file refactor. A strong non-frontier model degrades somewhere
around three. Do not infer a number from benchmark scores: agentic coding
benchmarks score single self-contained tasks, not multi-file coherence, and locally
the variables that actually move are quantization and the context cap you accepted
to fit the weights. A Q6 build capped at 128K and a Q4 build capped at 32K are two
different implementers with one model name.

The limit is coherence, not context length: a model with 128K context can still
lose the thread at file four.

## Procedure (about thirty minutes)

1. Take a real completed multi-file task from the repo's history.
2. Give the model the approved spec scoped to N files and run it.
3. Score by check script, and separately by whether the last file it touched is
   still consistent with the first.
4. Halve N on failure. Stop at the largest N that passes twice.

## Recording the result

Record it where the next plan will find it: the plan frontmatter's `implementer:`
(model, quantization, context cap) and `max_files:`. A plan for the same
configuration then sizes its subtasks from the measurement rather than a guess.
