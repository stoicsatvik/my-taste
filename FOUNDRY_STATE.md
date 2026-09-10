# My Taste — Unified Foundry State

## Mission
Build a local-first, user-owned multimodal preference layer that predicts what a user would choose, then exposes that learned taste to AI agents through MCP.

Core objective: `P(candidate_i > candidate_j | user, domain, context, evidence, history)`.

## Current status
**Claim status: SUPPORTED** for the frozen v0.1 text baseline and deterministic V0.2 context/provenance integration behavior. V0.2 is **NOT YET PROVEN** superior to v0.1.

### Frozen v0.1 baseline
- SQLite evidence persistence
- explicit pairwise choice learning
- edit-as-preference learning
- interpretable text features
- candidate ranking, explanations/confidence, CLI, MCP bindings
- deterministic tests

### V0.2 challenger — `feat/v0.2-context-provenance`
- exact context normalization and context-conditioned residual weights
- context-aware ranking/profile
- context-filtered provenance retrieval
- agent-facing `taste_context` compiler and MCP-v2 entrypoint
- deterministic context/provenance tests and context-separation smoke benchmark
- exact-head CI at `fd9ca123734c2784be708d20eceea169d4836ba5`: SUPPORTED integration behavior

### TasteBench V0.2 promotion experiment
Objective: test whether contextual V0.2 beats frozen v0.1 under an identical evidence budget on held-out pairwise choices.

Fixture: `synthetic-context-conflict-v1` in `benchmarks/tastebench_v02.py`.
- 4 training pairs per model, identical order/evidence budget
- 4 disjoint-wording held-out pairs
- two contexts with deliberately opposing style preferences
- metrics: pairwise accuracy and Brier score
- preregistered gate: V0.2 must have strictly higher held-out accuracy AND lower Brier score than v0.1
- no private/user evidence; fixture is synthetic

Experiment head after CI wiring: `85b69d86e4fe60c55585b28fb206057331aa16ab`.
Status: **NOT YET PROVEN** until exact-head CI executes the benchmark. Do not tune the fixture after seeing results; preserve failures and create a separately versioned challenger if needed.

## Foundry doctrine
1. Preserve simple baselines while introducing challengers.
2. Evaluate held-out pairwise choices before personalization claims.
3. Raw personal evidence is local-first; public fixtures are synthetic, consented, or safely anonymized.
4. Every learned preference retains provenance.
5. Separate domains/contexts; do not silently generalize across them.
6. Track uncertainty, contradictions, drift, abstention, and domain leakage.
7. Never commit private messages, screenshots, credentials, sensitive exports, or identifying datasets.

## Highest-priority sequence
### V0.2 — Context + provenance
Context scoring and provenance exist. Remaining gates: benchmark result, contradiction/drift handling, calibration/abstention, export/import, domain permission scopes, pluggable encoder, real MCP-client interoperability.

### V0.3 — Screenshots + images
Blocked on V0.2 benchmark foundation. Add image evidence schema, perceptual metadata, vision adapter, visual dimensions, pairwise ranking, sealed visual TasteBench only after V0.2 measurement is credible.

### V0.4 — Video + audio
Blocked on V0.3 evidence. Require multimodal gains over matched single-modality baselines.

### V0.5 — Portable taste layer
SDKs, scoped permissions, browser feedback capture, agent-readable resources, importers.

## TasteBench research track
Matched-budget comparison targets: no-context base, written profile, memory/RAG, v0.1 ranker, contextual My Taste, multimodal My Taste.
Metrics: pairwise accuracy, Brier/calibration, abstention quality, sample efficiency, drift adaptation, domain leakage.

## Current blockers / unknowns
- Exact-head `synthetic-context-conflict-v1` benchmark result pending CI.
- No contradiction/drift model yet.
- No screenshot/image implementation yet.
- MCP integration needs real compatible-client interoperability validation.
- No real/consented external preference benchmark yet.

## Next best move
Observe exact-head TasteBench CI. Promote V0.2 only if the preregistered matched-budget gate passes; otherwise preserve the failure and diagnose the model rather than tuning the holdout.
