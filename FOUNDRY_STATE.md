# My Taste — Unified Foundry State

## Mission
Build a local-first, user-owned preference layer optimizing `P(candidate_i > candidate_j | user, domain, context, evidence, history)`.

## Frozen baseline
- v0.1 baseline commit: `8b2a69b6c64962c11a9372e6940800579fe36fd6`
- Evidence: SQLite persistence, pairwise/edit learning, interpretable text ranking, CLI/MCP, 5 deterministic tests reported passing before V0.2.
- Status: **SUPPORTED / FROZEN BASELINE**.

## Current challenger
- Branch: `foundry/v0.2-context-benchmark`
- Implementation head before this ledger update: `7806f6d6b9e443ffe79a87e8e606568b21ee749a`
- Objective: context-conditioned preference learning plus matched held-out pairwise evaluation.
- Added: normalized context-specific weight overlays while retaining domain-global weights; context-aware pairwise probability; deterministic synthetic benchmark comparing no-context vs contextual scoring with accuracy and Brier metrics; tests for same-pair context reversal and cross-domain isolation.
- Added sealed TasteBench foundation: two deterministic synthetic context families, four sealed pairwise choices whose exact wording is absent from training evidence, matched no-context/context evaluation, and deterministic/disjointness/metric-bound tests.
- Privacy boundary: all benchmark fixtures are synthetic. No private chats, screenshots, exports, credentials, or identifying user evidence are committed.

## Validation / claim boundary
- Architecture: **SUPPORTED** by code inspection and deterministic test contracts.
- Sealed benchmark design: **SUPPORTED / SMALL**. Exact held-out wording is disjoint from training fixtures, but four sealed pairs are only a falsification foundation, not evidence of general personalization.
- Runtime result at challenger head: **NOT YET PROVEN**. No workflow run exists for the prior challenger head and the new TasteBench tests have not executed in this foundry cycle, therefore no accuracy/Brier numbers are claimed.
- Promotion: **NOT YET PROVEN**. v0.2 must beat or materially improve calibration over frozen v0.1 on deterministic sealed evaluation under matched evidence budgets and preserve v0.1 tests.
- MCP interoperability: **NOT YET PROVEN**.

## Blockers / falsification targets
1. Execute all baseline + challenger tests and `run_sealed_context_benchmark()`.
2. Expand sealed TasteBench beyond four pairs and add explicit promotion thresholds before interpreting gains.
3. Measure accuracy, Brier/calibration, abstention, sample efficiency, context drift and domain leakage under matched budgets.
4. Add provenance retrieval and contradiction/drift tracking only after the benchmark can expose regressions.

## Highest-EV next move
Execute the full suite and sealed benchmark. If green, enlarge deterministic sealed context families and preregister promotion thresholds; do not add vision until V0.2 has measured evidence.
