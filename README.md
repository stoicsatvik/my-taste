# My Taste

**A local-first, user-owned preference layer for AI agents.**

My Taste learns what a person would choose from evidence such as pairwise decisions, edits, messages, screenshots, images, audio, and video, then exposes that preference model to AI agents through MCP.

The core question is not **"What does the user remember?"** It is:

> **"Given several possible outputs, which one would this user prefer, in this context, and why?"**

## Why this exists

Most AI personalization is either a profile, a bag of memories, or hidden recommender-system state owned by a platform. My Taste is intended to be portable infrastructure owned by the user.

The long-term target is a multimodal taste function:

```text
T(user, candidate, context, history) -> preference score
```

Apps and agents should be able to ask My Taste for only the slice they need: writing, design, music, code, video, products, or another domain.

## v0.1: working text preference engine

The first version deliberately starts with a narrow loop that can be tested:

1. Observe a choice between preferred and rejected text.
2. Extract interpretable features from both.
3. Update a per-domain online preference model.
4. Rank unseen candidates.
5. Explain the strongest learned preference contributions.
6. Persist evidence and weights locally in SQLite.
7. Expose the loop through MCP tools.

An edit is treated as a strong pairwise signal: **edited text > original text**.

### Preference update

For preferred candidate `x+` and rejected candidate `x-`, My Taste uses an online Bradley-Terry/logistic-style update:

```text
delta = features(x+) - features(x-)
p     = sigmoid(weights · delta)
weights <- weights + learning_rate * (1 - p) * delta
```

This is intentionally simple and inspectable. Later versions can swap in learned multimodal encoders and richer ranking models without changing the evidence contract.

## Install

```bash
pip install -e ".[dev]"
```

The MCP dependency targets the current MCP Python SDK v2 line.

## Quick start

```bash
my-taste observe-choice \
  --preferred "Your website should make the offer obvious in five seconds." \
  --rejected "Transform your digital presence with next-generation solutions."

my-taste profile

my-taste rank \
  "Build something people can understand immediately." \
  "Leverage innovative solutions to unlock digital transformation."
```

The default database is `~/.my_taste/taste.db`. Override it with:

```bash
export MY_TASTE_DB=/path/to/taste.db
```

## MCP

Run the server:

```bash
my-taste-mcp
```

or during development:

```bash
mcp dev src/my_taste/mcp_server.py
```

Initial MCP tools:

- `observe_choice`
- `observe_edit`
- `rank_text`
- `taste_profile`
- `explain_text`

## Architecture

```text
Evidence
  |
  +-- text choices / edits        (implemented)
  +-- screenshots / images       (adapter contract)
  +-- audio / video              (adapter contract)
  +-- behavioral events          (adapter contract)
  |
  v
Feature extraction / embeddings
  |
  v
Preference engine
  |
  +-- local evidence store
  +-- domain-scoped weights
  +-- ranking + explanation
  |
  v
MCP / CLI / future SDKs
```

## Design principles

- **Local first**: raw personal evidence should not need a cloud service.
- **User owned**: export and deletion should be boring and complete.
- **Evidence backed**: every learned preference should be traceable to observations.
- **Contextual**: writing taste should not silently become music taste.
- **Uncertain by default**: weak evidence should remain weak evidence.
- **Replaceable models**: storage and protocol should survive model upgrades.
- **Scoped access**: future agents should request only the preference domains they need.

## Roadmap

See [`ROADMAP.md`](ROADMAP.md).

## Status

Experimental. v0.1 is a real baseline, not a claim that human taste can be compressed into eight lexical features without embarrassing consequences.

## License

MIT
