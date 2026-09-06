# My Taste — Unified Foundry State

## Mission

Build a local-first, user-owned multimodal preference layer that predicts what a user would choose, then exposes that learned taste to AI agents through MCP.

Core objective:

`P(candidate_i > candidate_j | user, domain, context, evidence, history)`

This is a preference-learning system, not merely a memory store.

## Current status

**Claim status: SUPPORTED**

v0.1 has a working text preference baseline:

- SQLite evidence persistence
- explicit pairwise choice learning
- edit-as-preference learning
- interpretable text feature extraction
- candidate ranking
- explanations and confidence estimates
- CLI
- MCP server bindings
- deterministic unit tests

Current baseline tests: 5 passing.

## Foundry doctrine for this repo

1. Make substantive tested progress, not cosmetic commits.
2. Preserve a simple baseline while introducing stronger challengers.
3. Evaluate on held-out pairwise choices before claiming personalization gains.
4. Keep raw personal evidence local-first by default.
5. Every learned preference must retain provenance to its evidence.
6. Separate domains and contexts; do not silently generalize writing taste into unrelated domains.
7. Track uncertainty, contradictions, preference drift, and abstention rather than forcing confident predictions.
8. Prefer pluggable encoders/rankers so the protocol and evidence store survive model changes.
9. Never commit private user evidence, message exports, screenshots, credentials, or sensitive personal datasets to this public repository.
10. Public fixtures must be synthetic, consented, or safely anonymized.

## Highest-priority build sequence

### V0.2 — Context + provenance

- context tags and context-conditioned scoring
- provenance retrieval API
- contradiction tracking
- preference confidence/calibration
- JSON export/import
- domain permission scopes
- pluggable text encoder interface
- held-out pairwise benchmark harness

Promotion gate: context-aware challenger must outperform or materially improve calibration over v0.1 on deterministic/sealed evaluation without breaking existing tests.

### V0.3 — Screenshots + images

- image/screenshot evidence schema
- perceptual hash + metadata
- vision adapter interface
- visual preference dimensions such as hierarchy, density, spacing, typography, composition
- pairwise visual ranking
- image TasteBench fixtures

Promotion gate: demonstrate reproducible held-out visual preference prediction above simple metadata/profile baselines.

### V0.4 — Video + audio

- frame/scene sampling
- transcript ingestion
- pacing/editing features
- audio adapter
- multimodal fusion

Promotion gate: multimodal model must beat single-modality baselines on sealed held-out choices under matched budgets.

### V0.5 — Portable taste layer

- Python/TypeScript SDKs
- agent-readable resources
- scoped taste permissions
- browser extension feedback capture
- platform-history importers

## Research track — TasteBench

Compare under matched evidence and budgets:

1. base model with no user context
2. written preference profile
3. RAG over user memories
4. My Taste v0.1 interpretable ranker
5. contextual My Taste
6. multimodal My Taste

Primary metrics:

- pairwise preference accuracy
- calibration / Brier score
- abstention quality
- sample efficiency
- adaptation to preference drift
- domain leakage / unwanted generalization

## Current blockers / unknowns

- No context-conditioned model yet.
- No sealed benchmark dataset yet.
- No screenshot/image implementation yet.
- No contradiction/drift model yet.
- MCP integration exists but needs client-side interoperability validation.

## Next best move

Build V0.2 context-conditioned preference learning plus a deterministic held-out pairwise benchmark before adding vision complexity.
