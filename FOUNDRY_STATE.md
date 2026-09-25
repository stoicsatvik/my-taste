# My Taste — Unified Foundry State

## Mission

Build a local-first, user-owned multimodal preference layer that predicts what a user would choose and gives AI agents the right preference context at the right moment.

Core objective:

`P(candidate_i > candidate_j | user, domain, context, evidence, history)`

This is a preference-learning and retrieval system, not merely a memory store.

## Current status

**Claim status: SUPPORTED WITH BOUNDED MULTIMODALITY**

The repository now has two working layers.

### Pairwise text model

- explicit pairwise choice learning
- edit-as-preference learning
- interpretable lexical feature extraction
- online preference weights
- raw text ranking and explanation

### Contextual structured evidence layer

- universal multimodal `TasteEvidence`
- domain and modality separation
- structured context tags
- positive / negative artifact preferences
- provenance references
- relevance-ranked contextual retrieval
- generic structured candidate ranking
- CLI and MCP exposure
- Agent Skill workflows for writing, websites/UI, and video references

The multimodal path is currently **agent-mediated**:

`agent perception -> structured fingerprint -> My Taste persistence/retrieval`

The core does not yet directly run computer vision, frame extraction, or audio analysis.

## Foundry doctrine

1. Make substantive tested progress, not cosmetic commits.
2. Preserve simple baselines while introducing stronger challengers.
3. Evaluate on held-out choices before claiming personalization gains.
4. Keep private evidence local-first by default.
5. Every learned preference retains provenance.
6. Context is part of taste; do not silently generalize across domains or surfaces.
7. Track uncertainty, contradiction, drift, and abstention rather than forcing confidence.
8. Keep perception adapters replaceable so evidence survives model/provider changes.
9. Never commit private user evidence, exports, screenshots, credentials, or sensitive datasets to this public repo.
10. Public fixtures must be synthetic, consented, or safely anonymized.

## Current capability path

### Website / UI

```text
user likes page
  -> capable agent inspects page/screenshots
  -> extracts design grammar
  -> observe_artifact(ui_design, website, ...)
  -> future UI task
  -> retrieve_taste(ui_design, task context)
  -> apply / rank candidate fingerprints
```

### Writing

```text
single liked sample
  -> style fingerprint
  -> observe_artifact(writing, text, ...)

pairwise choice or edit
  -> lexical online learner
  -> stronger comparative signal
```

### Video

```text
user likes video
  -> capable agent samples multiple moments
  -> extracts editing/narrative/visual/audio fingerprint
  -> observe_artifact(video, video, ...)
  -> future matching video task
  -> retrieve_taste(video, platform/format/goal)
```

## Highest-priority next sequence

### 1. Contradiction + confidence

- feature-level support counts
- conflicting positive/negative evidence
- calibrated confidence
- explicit abstention threshold
- preference drift handling

### 2. Direct local perception adapters

UI/image:
- screenshot metadata
- perceptual hashes
- pluggable vision encoder
- automated fingerprint extraction

Video:
- frame/scene sampling
- measured cuts / shot duration
- transcript ingestion
- audio feature adapter

### 3. TasteBench

Compare under matched evidence and budgets:

1. base model
2. written preference profile
3. memory/RAG
4. pairwise lexical My Taste
5. contextual structured My Taste
6. direct multimodal My Taste

Metrics:
- pairwise preference accuracy
- calibration / Brier score
- abstention quality
- sample efficiency
- adaptation to preference drift
- domain leakage

## Current blockers / unknowns

- No calibrated contradiction/drift model yet.
- No sealed contextual benchmark yet.
- No direct local vision/video extraction yet.
- No embedding-backed semantic retrieval yet.
- Remote MCP interoperability still needs end-to-end client validation.

## Next best move

Validate the new contextual evidence layer end-to-end through ChatGPT/MCP, then add direct video/UI perception adapters behind the same evidence contract.
