# My Taste — Unified Foundry State

## Mission
Build a local-first, user-owned preference layer optimizing `P(candidate_i > candidate_j | user, domain, context, evidence, history)`.

## Frozen baseline
- v0.1 baseline commit: `8b2a69b6c64962c11a9372e6940800579fe36fd6`
- Evidence: SQLite persistence, pairwise/edit learning, interpretable text ranking, CLI/MCP, 5 deterministic tests reported passing before V0.2.
- Status: **SUPPORTED / FROZEN BASELINE**.

## Current challenger
- Branch: `foundry/v0.2-context-benchmark`
- Implementation head before this ledger update: `2fe79ee4f02caae2a434ea5270bb8fcaab500252`
- Objective: context-conditioned preference learning plus matched held-out pairwise evaluation.
- Added: normalized context-specific weight overlays while retaining domain-global weights; context-aware pairwise probability; deterministic synthetic benchmark comparing no-context vs contextual scoring with accuracy and Brier metrics; tests for same-pair context reversal and cross-domain isolation.
- Added sealed TasteBench foundation: two deterministic synthetic context families, four sealed pairwise choices whose exact wording is absent from training evidence, matched no-context/context evaluation, and deterministic/disjointness/metric-bound tests.
- Added explicit domain-leakage falsification: train writing preferences repeatedly while measuring an untouched design-domain control on the identical pair/context.
- Added preregistered V0.2 promotion protocol and executable fail-closed gate before enlarging the sealed set. Minimum 32 sealed pairs; all baseline/challenger tests; deterministic leakage <= 1e-12; plus either >=0.05 accuracy gain or <=0.02 accuracy regression with >=0.02 Brier improvement. Threshold revisions require a new protocol version and newly sealed set.
- Privacy boundary: all benchmark fixtures are synthetic. No private chats, screenshots, exports, credentials, or identifying user evidence are committed.

## Validation / claim boundary
- Architecture: **SUPPORTED** by code inspection and deterministic test contracts.
- Sealed benchmark design: **SUPPORTED / SMALL**. Four sealed pairs are only a falsification foundation and are now explicitly incapable of promotion under the preregistered 32-pair floor.
- Promotion protocol: **SUPPORTED BY FROZEN CONTRACT / NOT YET EXECUTED AT THIS HEAD**. Thresholds were fixed before benchmark enlargement to reduce post-result tuning.
- Runtime result at challenger head: **NOT YET PROVEN**. No accuracy/Brier/leakage numbers are claimed without execution.
- Promotion: **NOT YET PROVEN / AUTOMATICALLY BLOCKED AT CURRENT SAMPLE SIZE**.
- MCP interoperability: **NOT YET PROVEN**.

## Blockers / falsification targets
1. Execute all baseline + challenger tests, `run_sealed_context_benchmark()`, and `run_domain_leakage_check()`.
2. Expand sealed TasteBench from 4 to >=32 genuinely held-out synthetic pairs without changing the frozen V0.2 protocol.
3. Measure accuracy, Brier/calibration, abstention, sample efficiency and context drift under matched budgets.
4. Add provenance retrieval and contradiction/drift tracking only after the benchmark can expose regressions.

## Highest-EV next move
Execute the full suite and both benchmark gates. Regardless of the four-pair smoke result, promotion remains blocked by the preregistered sample floor. Then enlarge the sealed set without changing thresholds; do not add vision until V0.2 has measured evidence.
