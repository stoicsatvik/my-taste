# My Taste roadmap

## v0.1 — Pairwise text preference loop

- [x] Local SQLite evidence store
- [x] Interpretable text feature extractor
- [x] Pairwise online preference learning
- [x] Treat edits as preference pairs
- [x] Candidate ranking
- [x] Preference explanations
- [x] MCP server
- [x] CLI
- [x] Unit tests

## v0.2 — Contextual evidence layer

- [x] Universal structured `TasteEvidence` object
- [x] Domain + modality separation
- [x] Context tags
- [x] Context-aware retrieval
- [x] Source provenance references
- [x] Positive and negative artifact evidence
- [x] Generic structured profile ranking
- [x] MCP tools for artifact observation and retrieval
- [x] CLI support for structured evidence
- [ ] Contradiction tracking
- [ ] Calibrated confidence / abstention
- [ ] JSON export/import
- [ ] Domain permission scopes
- [ ] Embedding-backed semantic retrieval
- [ ] Held-out contextual benchmark harness

## v0.3 — Websites, screenshots, and images

- [x] Agent-mediated UI/website fingerprint contract
- [x] Reusable UI dimensions: density, hierarchy, typography, spacing, palette, composition, motion
- [x] Contextual UI retrieval through the generic evidence layer
- [x] Generic candidate profile ranking for visual fingerprints
- [ ] Direct local screenshot/image evidence object with blob metadata
- [ ] Screenshot metadata + perceptual hash
- [ ] Local/pluggable vision adapter interface
- [ ] Automated screenshot fingerprint extraction
- [ ] Image TasteBench fixtures

## v0.4 — Video and audio

- [x] Agent-mediated video fingerprint contract
- [x] Video preference storage and contextual retrieval
- [x] Video dimensions: hook, pacing, cuts, captions, camera, transitions, color, audio, retention mechanics
- [x] Generic ranking for video candidate fingerprints
- [ ] Direct local video sampling pipeline
- [ ] Scene boundary detection
- [ ] Measured pacing / shot-length extraction
- [ ] Transcript ingestion pipeline
- [ ] Local/pluggable audio feature adapter
- [ ] Multimodal fusion model
- [ ] Video TasteBench fixtures

## v0.5 — Portable taste layer

- [ ] Python SDK
- [ ] TypeScript SDK
- [ ] Agent-readable preference resources
- [ ] Scoped capability grants by taste domain
- [ ] Browser extension for "prefer this / reject that"
- [ ] Importers for exported platform history
- [ ] Remote MCP deployment reference

## Product surface — Tasteprint

Tasteprint is a feature of My Taste, not a separate preference system. See [`docs/TASTEPRINT.md`](docs/TASTEPRINT.md).

- [ ] Pairwise onboarding session backed by normal My Taste evidence
- [ ] Interpretable Tasteprint result with confidence
- [ ] `taste.json` export
- [ ] compact `taste.md` agent-context export
- [ ] local web/CLI experience
- [ ] opt-in public share page and share-card renderer
- [ ] handoff into MCP/SDK setup

## Research track — TasteBench

Measure unseen pairwise preference prediction accuracy for:

1. Base LLM with no user context
2. Written preference profile
3. RAG over user memories
4. My Taste pairwise lexical model
5. My Taste contextual structured evidence
6. Multimodal My Taste with direct perception adapters

Primary metric: held-out pairwise accuracy.
Secondary metrics: calibration, abstention quality, data efficiency, drift adaptation, and domain leakage.
