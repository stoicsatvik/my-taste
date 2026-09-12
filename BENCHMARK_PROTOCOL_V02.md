# V0.2 promotion protocol

This protocol is frozen before enlarging the sealed benchmark. Its purpose is to prevent post-result threshold tuning.

## Compared systems

- Champion: frozen v0.1/no-context scoring.
- Challenger: V0.2 context-conditioned scoring.
- Evidence budget, training pairs, candidate pairs, domains, and evaluation order must be matched.
- Sealed candidate wording must not appear in training evidence.

## Hard gates

V0.2 cannot be promoted unless all of the following hold:

1. At least 32 sealed pairwise choices are evaluated.
2. Baseline regression tests pass.
3. Challenger regression tests pass.
4. Absolute cross-domain leakage is <= 1e-12 in the deterministic leakage check.
5. At least one evidence path passes:
   - accuracy path: V0.2 pairwise accuracy exceeds v0.1 by >= 0.05; or
   - calibration path: V0.2 accuracy regresses by no more than 0.02 and Brier score improves by >= 0.02.

These are engineering promotion gates, not statistical claims of population-level superiority. The 32-pair floor is a minimum falsification surface, not a power calculation.

## Required reporting

Record exact commit, benchmark fixture version/hash, sealed-pair count, v0.1 and V0.2 accuracy, v0.1 and V0.2 Brier score, leakage result, test result, and promotion decision. Preserve failures. Do not alter thresholds after seeing sealed results; any threshold revision requires a new protocol version and a newly sealed evaluation set.

## Deferred metrics

Abstention quality, sample efficiency, drift adaptation, and stronger calibration diagnostics remain required V0.2 research targets, but they are not silently smuggled into this first promotion decision after results are visible. They require explicit benchmark extensions and versioned gates.
