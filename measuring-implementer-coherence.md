# Measuring an implementer's coherence limit

A one-off calibration job, run once per implementer configuration. It is not part of
writing a plan: a plan uses the result (`max_files:`) or the default, never a
measurement taken on the spot.

## Why measure

Coherence limits are per implementer, and per build for a local model. As rough
experience, not a measurement: a frontier model holds a ten-file refactor, and a
strong non-frontier model degrades somewhere around three. That spread is why the
number has to be measured. Do not infer it from benchmark scores: agentic coding
benchmarks score single self-contained tasks, not multi-file coherence, and locally
the variables that actually move are quantization and the context cap you accepted
to fit the weights. A Q6 build capped at 128K and a Q4 build capped at 32K are two
different implementers with one model name.

The limit is coherence, not context length: a model with 128K context can still
lose the thread at file four.

## Procedure (about thirty minutes)

1. Take a real completed multi-file task from the repo's history. Start with N equal
   to the number of files it touched.
2. Give the model the approved spec scoped to N files and run it.
3. Score by check script, and separately by reading whether the last file it
   touched is still consistent with the first. The second score is a judgement;
   write down what you compared.
4. Bisect: on a failure try half of N, on a pass try halfway back up. Stop at the
   largest N that passes twice.

## Recording the result

Record it where the next plan will find it, as a line that Rule 4's
`grep -rn '^max_files:' docs/` matches, in the plan being written or in
`docs/plans/implementers.md`:

```
max_files: 3  # measured 2026-09-23, qwen3-coder-30b-a3b Q4_K_M, 32K context
```

A plan for the same model, quantization and context cap then sizes its subtasks
from the measurement rather than a guess. A different quantization or context cap
is a different implementer and needs its own line.
