# My Taste roadmap

## v0.1 — Preference loop

- [x] Local SQLite evidence store
- [x] Interpretable text feature extractor
- [x] Pairwise online preference learning
- [x] Treat edits as preference pairs
- [x] Candidate ranking
- [x] Preference explanations
- [x] MCP server
- [x] CLI
- [x] Unit tests

## v0.2 — Evidence + context

- [ ] Context tags and context-conditioned weights
- [ ] Evidence provenance API
- [ ] Preference confidence and contradiction tracking
- [ ] JSON export/import
- [ ] Domain permission scopes
- [ ] Better text embeddings behind a pluggable encoder interface

## v0.3 — Screenshots and images

- [ ] Image evidence object
- [ ] Screenshot metadata + perceptual hash
- [ ] Vision adapter interface
- [ ] Extract design dimensions: density, hierarchy, typography, spacing, composition
- [ ] Pairwise visual ranking
- [ ] Image taste benchmark

## v0.4 — Video and audio

- [ ] Video sampling pipeline
- [ ] Scene boundaries and pacing features
- [ ] Transcript ingestion
- [ ] Audio feature adapter
- [ ] Multimodal preference fusion

## v0.5 — Portable taste layer

- [ ] SDKs for Python and TypeScript
- [ ] Agent-readable preference resources
- [ ] Scoped capability grants by taste domain
- [ ] Browser extension for "prefer this / reject that"
- [ ] Importers for exported platform history

## Research track — TasteBench

Measure unseen pairwise preference prediction accuracy for:

1. Base LLM with no user context
2. Written preference profile
3. RAG over user memories
4. My Taste evidence + ranking model
5. Multimodal My Taste

Primary metric: pairwise accuracy on held-out user choices.
Secondary metrics: calibration, abstention quality, data efficiency, preference drift adaptation.
