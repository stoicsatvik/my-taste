---
name: my-taste
description: Apply the user's learned My Taste preference model when ranking, selecting, revising, or explaining candidate outputs. Use when the user asks what they would prefer, asks to make an output fit their taste, wants candidates ranked by learned preferences, or gives an explicit choice/edit that should update the preference model. Use persisted preferences only through the My Taste MCP tools; never invent learned taste when those tools or evidence are unavailable.
---

# My Taste

Use My Taste as a **preference layer**, not as a personality profile or memory substitute.

The system models:

`P(candidate_i > candidate_j | user, domain, context, evidence, history)`

Its job is to help choose between plausible outputs according to evidence-backed user preferences while preserving uncertainty, provenance, and domain boundaries.

## Core rules

1. **Separate task quality from user taste.**
   First satisfy the user's explicit request, factual constraints, safety requirements, and technical correctness. Use My Taste only to choose among outputs that already satisfy those requirements.

2. **Use persisted taste only through My Taste tools.**
   Do not claim the user prefers something because of general chat memory, demographic assumptions, stereotypes, or an invented profile.

3. **Do not generalize across domains.**
   A preference learned in `writing` is not evidence about design, music, products, code, video, or another domain. If a requested domain is unsupported or has insufficient evidence, state that the model does not yet have enough evidence rather than fabricating a prediction.

4. **Learn only from explicit preference evidence.**
   Record a preference when the user:
   - explicitly chooses A over B,
   - says they prefer one candidate to another,
   - rewrites/edits an output and the original plus edited version are available,
   - explicitly asks My Taste to learn the preference.

   Do not learn from silence, mere task completion, politeness, assistant guesses, or an output the user has not evaluated.

5. **Keep raw evidence private by default.**
   Never expose the underlying preference database or unrelated evidence merely to justify a ranking. Return derived preferences or the minimum provenance needed for the request.

Read `references/tool-contract.md` before using the MCP tools when the tool behavior or evidence boundary is unclear.

## Ranking workflow

When the user provides multiple text candidates and asks which best matches their taste:

1. Confirm the domain. Use `writing` for prose, captions, messages, scripts, copy, and similar text unless the user specifies another supported domain.
2. Call `rank_text` with all viable candidates.
3. Return the highest-ranked candidate.
4. If useful, briefly explain the strongest learned contributions. Do not drown a simple choice in a personality autopsy.
5. If scores are effectively tied or the model has weak evidence, preserve the uncertainty instead of manufacturing certainty.

## Generate-to-taste workflow

When the user asks for a new text output that should match their taste:

1. Satisfy the explicit content requirements first.
2. Call `taste_profile` for the relevant domain.
3. Generate a small internal candidate set that varies meaningfully on the strongest learned dimensions.
4. Call `rank_text` on those candidates.
5. Return the best candidate. Do not expose the internal candidate set unless comparison would help the user.
6. Use `explain_text` only when an explanation is requested or when the top choice is surprising.

Do not let the taste model override explicit user instructions from the current request.

## Learning workflow

### Explicit pairwise choice

When the user clearly prefers one text candidate over another, call:

`observe_choice(preferred, rejected, domain, context)`

The `context` should be short and decision-relevant, such as `landing-page headline`, `cold outreach`, or `Instagram caption`. Do not dump an entire private conversation into context.

### User edit

When the user changes a known original into an edited version and the edit expresses preference, call:

`observe_edit(original, edited, domain, context)`

Treat the edit as `edited > original`. Do not infer additional preferences that are not supported by the edit.

## Profile and explanation workflow

Use `taste_profile` when the user asks what the model has learned.

Describe results as learned tendencies, for example:

- "The current writing evidence favors..."
- "The model has repeatedly learned..."
- "Confidence is still weak on..."

Avoid essentialist claims such as "you are the kind of person who..." or universal statements that exceed the evidence.

Use `explain_text` when the user asks why a candidate fits or conflicts with learned taste. Explain the strongest positive and negative feature contributions, not a fictional psychological story.

## Failure and abstention behavior

If the My Taste tools are unavailable, the database is empty, or the requested domain is unsupported:

- do not pretend a persisted preference model exists,
- do not convert generic memory into "learned My Taste",
- complete the underlying task normally using explicit instructions from the current conversation,
- state the limitation only when it materially affects the answer.

## Current implementation boundary

The repository's v0.1 engine implements interpretable **text/writing** preference learning. Visual, code, music, product, audio, and video taste are roadmap domains until their evidence adapters and benchmarks are implemented.

Prefer a narrow, honest prediction over a grand personalized hallucination.
