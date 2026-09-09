# Temporal Policy Promotion Protocol v0.1

Status: **FROZEN BEFORE ADVERSARIAL EXECUTION**

This protocol selects whether a bounded-history temporal policy is worth advancing beyond benchmark-only status. It does not modify the production learner and makes no real-user claim.

## Frozen champion

- Accumulating V0.2 context learner at `de19030024830de7c85c53462bd989f104b7c6b7`.
- Existing evidence: contextual TasteBench promotion passed; asymmetric DriftBench exposed stale-history inertia.

## Candidate policies

Bounded histories of 4, 8, 16, and 32 observations. No other window may be introduced after adversarial results are observed under this protocol.

## Frozen adversarial regimes

Each candidate must be evaluated on identical synthetic observation budgets in all regimes:

1. **Context-local reversal**: one context reverses while a neighboring context in the same domain remains stable.
2. **Repeated oscillation**: preference direction alternates in four equal phases of 8 observations.
3. **Source conflict**: two synthetic provenance sources provide opposing choices with equal observation counts; evaluation must preserve source labels and report confidence rather than silently treating agreement as established preference.
4. **Long-history reversal**: preserve the existing `(8,2), (32,2), (128,2), (32,8), (128,8)` matrix unchanged.
5. **Stable retention**: matched non-drifting streams for every applicable budget.

Fixtures must remain synthetic and deterministic. Candidate strings used for this gate must not contain private user evidence.

## Metrics

Report, without selective omission:

- mean and worst post-drift Brier;
- stable-preference Brier;
- first update at which the new preference exceeds 0.5 after reversal;
- neighboring-context probability delta under context-local reversal;
- oscillation phase-end accuracy and Brier;
- source-conflict probability and distance from 0.5.

## Promotion gate

A bounded-history policy may advance to a production-learner implementation challenger only if all of the following hold:

1. deterministic tests and the frozen V0.2 context/leakage gates pass;
2. mean post-drift Brier improves by at least 25% relative to the accumulator over the frozen long-history reversal matrix;
3. worst stable-preference Brier is <= 0.005;
4. absolute neighboring-context probability delta is <= 0.02;
5. oscillation phase-end accuracy is >= 0.75;
6. under equal-count source conflict, absolute distance from 0.5 is <= 0.15;
7. no metric is NaN, omitted, or computed from an empty case set.

If multiple policies pass, select the policy with the lowest mean post-drift Brier. Ties within `1e-12` select the larger window to preserve more history.

If no policy passes, bounded-history production integration is **REJECTED under this protocol** and the next challenger should use provenance-aware/adaptive weighting rather than threshold surgery.

## Change control

Thresholds, windows, regimes, and tie-breaking are frozen once this file is committed. Any revision requires `TEMPORAL_PROMOTION_PROTOCOL_V02.md` and a newly sealed adversarial fixture before seeing its results. Do not edit v0.1 to rescue a losing candidate.

## Claim boundary

Passing this protocol supports only deterministic synthetic temporal robustness. It does not prove real-user drift adaptation, optimal memory length, population calibration, or MCP interoperability.
