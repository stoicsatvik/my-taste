# My Taste — Unified Foundry State

## Mission
Build a local-first, user-owned preference layer optimizing `P(candidate_i > candidate_j | user, domain, context, evidence, history)`.

## Frozen baseline
- v0.1 baseline commit: `8b2a69b6c64962c11a9372e6940800579fe36fd6`
- Evidence: SQLite persistence, pairwise/edit learning, interpretable text ranking, CLI/MCP, 5 deterministic tests reported passing before V0.2.
- Status: **SUPPORTED / FROZEN BASELINE**.

## Current challenger
- Branch: `foundry/v0.2-context-benchmark`
- Implementation head before this ledger update: `3937bfed2e7eb516920be59aa3d2d7a6a1e0f3e0`
- Objective: context-conditioned preference learning plus matched held-out pairwise evaluation.
- Added: normalized context-specific weight overlays while retaining domain-global weights; context-aware pairwise probability; deterministic synthetic benchmark comparing no-context vs contextual scoring with accuracy and Brier metrics; tests for same-pair context reversal and cross-domain isolation.
- TasteBench now contains 32 sealed synthetic choices across 8 context families. Exact candidate strings are withheld from training evidence; tests enforce train/sealed tuple disjointness, candidate-string disjointness, exact pair count, context-family count, determinism, and metric bounds.
- Added explicit domain-leakage falsification: train writing preferences repeatedly while measuring an untouched design-domain control on the identical pair/context.
- Frozen V0.2 promotion protocol: minimum 32 sealed pairs; baseline/challenger tests; deterministic leakage <= 1e-12; plus either >=0.05 accuracy gain or <=0.02 accuracy regression with >=0.02 Brier improvement. Threshold revisions require a new protocol version and newly sealed set.
- Privacy boundary: all benchmark fixtures are synthetic. No private chats, screenshots, exports, credentials, or identifying user evidence are committed.

## Validation / claim boundary
- Architecture: **SUPPORTED** by code inspection and deterministic test contracts.
- Sealed benchmark sample-floor architecture: **SUPPORTED / NOT YET EXECUTED AT THIS HEAD**. The fixture now reaches the preregistered 32-pair minimum and spans eight context families, but this is an engineering falsification surface, not a statistical population claim.
- Promotion protocol: **SUPPORTED BY FROZEN CONTRACT / NOT YET EXECUTED AT THIS HEAD**.
- Runtime result at challenger head: **NOT YET PROVEN**. No accuracy/Brier/leakage numbers are claimed without execution.
- Promotion: **NOT YET PROVEN**. Reaching the sample floor removes the automatic size veto but does not imply any evidence gate passes.
- MCP interoperability: **NOT YET PROVEN**.

## Blockers / falsification targets
1. Execute all baseline + challenger tests, `run_sealed_context_benchmark()`, and `run_domain_leakage_check()` at the 32-pair head.
2. Record exact accuracy/Brier/leakage outputs and apply the frozen promotion gate without threshold changes.
3. Add abstention and sample-efficiency benchmark extensions under versioned gates; measure context drift under matched budgets.
4. Add provenance retrieval and contradiction/drift tracking only after the benchmark can expose regressions.

## Highest-EV next move
Execute the full suite and both benchmark gates at the 32-pair head. Preserve the result whether flattering or ugly. Do not add vision until V0.2 has measured evidence.
