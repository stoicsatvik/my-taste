# My Taste — Unified Foundry State

## Mission
Build a local-first, user-owned preference layer optimizing `P(candidate_i > candidate_j | user, domain, context, evidence, history)`.

## Frozen baseline
- v0.1 baseline commit: `8b2a69b6c64962c11a9372e6940800579fe36fd6`
- Evidence: SQLite persistence, pairwise/edit learning, interpretable text ranking, CLI/MCP, 5 deterministic tests reported passing before V0.2.
- Status: **SUPPORTED / FROZEN BASELINE**.

## Current challenger
- Branch: `foundry/v0.2-context-benchmark`
- Head before this ledger update: `a278d894f8341d9ffcc5fe9052f690765cfd6d35`
- Objective: context-conditioned preference learning plus matched held-out pairwise evaluation.
- Added: normalized context-specific weight overlays while retaining domain-global weights; context-aware pairwise probability; deterministic synthetic benchmark comparing no-context vs contextual scoring with accuracy and Brier metrics; tests for same-pair context reversal and cross-domain isolation.
- Privacy boundary: benchmark fixtures are synthetic. No private chats, screenshots, exports, credentials, or identifying user evidence are committed.

## Validation / claim boundary
- Architecture: **SUPPORTED** by code inspection and deterministic test contracts.
- Runtime result at challenger head: **NOT YET PROVEN**. Tests have been committed but no runner result is available in this foundry cycle, therefore no benchmark numbers are claimed.
- Promotion: **NOT YET PROVEN**. v0.2 must beat or materially improve calibration over frozen v0.1 on a deterministic sealed benchmark under matched evidence budgets and preserve v0.1 tests.
- MCP interoperability: **NOT YET PROVEN**.

## Blockers / falsification targets
1. Execute all baseline + challenger tests.
2. Freeze a larger sealed synthetic pairwise split with contexts withheld from training examples rather than relying on the tiny smoke fixture.
3. Measure accuracy, Brier/calibration, abstention, sample efficiency, context drift and domain leakage under matched budgets.
4. Add provenance retrieval and contradiction/drift tracking only after the benchmark can expose regressions.

## Highest-EV next move
Run the full test suite and benchmark; if green, strengthen TasteBench with deterministic train/held-out splits and explicit no-context/context promotion thresholds before adding vision.
