# Tasteprint

Tasteprint is the consumer-facing onboarding and sharing surface for My Taste.

It is **not a separate preference engine**. It should use My Taste's evidence contract, domain separation, ranking, provenance, and export formats so every interaction improves or initializes the same portable preference model.

## Product loop

```text
pairwise choices
    -> My Taste observations
    -> preference profile
    -> Tasteprint result
    -> export / share / agent handoff
```

## v0 scope

1. Present a short sequence of pairwise choices.
2. Record each answer as normal My Taste preference evidence.
3. Generate an interpretable profile from learned weights and confidence.
4. Produce a compact Tasteprint result suitable for a web UI and share card.
5. Export the result as `taste.json` and a compact `taste.md` context file.
6. Provide a direct path into the MCP/SDK workflow.

Initial domains can start with text/writing because that engine already exists. Visual, code, product, music, video, and other domains should only ship when the corresponding evidence adapters are real and benchmarked.

## Privacy defaults

- Raw personal evidence remains private/local by default.
- Public Tasteprints require explicit opt-in.
- Shared results should expose derived preferences, not the underlying private evidence, unless the user explicitly chooses otherwise.
- Public fixtures and demos must be synthetic, consented, or safely anonymized.

## Proposed interfaces

Core API concept:

```python
session = engine.start_tasteprint(domain="writing")
session.observe(preferred=a, rejected=b, context={...})
result = session.result()
```

Result shape should contain at least:

```text
domain
preference dimensions / weights
confidence
strongest positive signals
strongest negative signals
provenance references (private by default)
export version
```

Potential product surfaces:

- `my-taste tasteprint` CLI flow
- local web UI
- hosted opt-in share page
- share-card renderer
- `taste.json` export
- `taste.md` export

## Success metrics

Tasteprint is an acquisition/onboarding surface, so measure:

- completion rate
- number of useful observations captured per completed session
- calibration / held-out preference accuracy after onboarding
- export rate
- share rate for explicitly public results
- MCP/SDK activation after completion

Do not optimize share rate at the cost of privacy, model quality, or misleading personality claims.

## Non-goals

Tasteprint is not:

- a horoscope-style personality test
- a replacement for TasteBench
- a separate user profile database
- permission to collapse unrelated preference domains into one score

The output should remain evidence-backed, contextual, uncertain when evidence is weak, and compatible with the same portable preference layer as the rest of My Taste.
