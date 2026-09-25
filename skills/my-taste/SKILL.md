---
name: my-taste
description: Learn and apply the user's explicit writing, UI, website, screenshot, and video preferences. Use when the user likes/dislikes a reference, asks to save/copy/learn a style, asks which candidate fits their taste, or requests taste-sensitive creative work. Prefer low-token one-shot save tools and compact taste retrieval.
---

# My Taste

My Taste is a durable, contextual preference layer. Explicit task requirements, correctness, and safety outrank taste.

## Cost rule

**Keep forensic detail in My Taste, not in the model transcript.**

For normal use, do not chain analysis tools if a one-shot save tool exists.

### Save a live website

When the user likes/dislikes a public website and wants it remembered:

1. Infer a compact context, e.g. `{"surface":"landing_page","industry":"saas","goal":"conversion"}`.
2. Call `save_website_reference` directly.
3. Do **not** call `analyze_website` first.
4. Return only a short confirmation.

`save_website_reference` performs deep browser/DOM/CSS/pixel/motion capture server-side, stores the large raw capture locally, saves a compact fingerprint, and returns a small receipt.

Use `analyze_website` only when the user explicitly asks to see/explain the forensic analysis itself.

### Save a screenshot/image

If a readable local path exists:

1. Inspect the image with host vision.
2. Create only a compact semantic fingerprint: layout, hierarchy, typography, spacing, component grammar, visual character, and other salient visible style.
3. Call `save_image_reference(path, semantic_features=...)`.
4. Do not call `analyze_image_file` first unless the user asks to see pixel analysis.

A still image has no time axis. Never infer animation, hover states, scroll effects, or timing from one screenshot.

If no local path is available, save the compact host fingerprint with `observe_artifact`.

### Save writing/video/other references

Use `observe_artifact` with a compact structured fingerprint. For explicit text A>B use `observe_choice`; for a known rewrite use `observe_edit`.

Do not store full copyrighted articles, transcripts, videos, or page contents as preference evidence. Store reusable style abstractions and minimal provenance.

## Apply taste

For normal taste-sensitive generation:

1. Infer domain and compact task context.
2. Call `taste_brief` once, normally with `limit=4` to `6`.
3. Apply high-confidence `prefer` rules, avoid `avoid` rules, and do not force conflicts.
4. Generate the output.

Do not call `retrieve_taste` unless the user asks for provenance or a specific stored reference. Do not dump the stored fingerprint into the conversation.

Domains:
- prose/copy/scripts/messages -> `writing`
- websites/apps/dashboards/visual systems -> `ui_design`
- reels/video/editing -> `video`

Context is part of taste. A Reel preference is not automatically a documentary preference; a landing-page preference is not automatically a dense admin-dashboard preference.

## Evidence rules

Learn only from explicit preference evidence:
- "I like this"
- "save this style"
- explicit dislike
- A > B choice
- direct user edit

Do not learn from silence, demographics, assistant guesses, or an output merely being generated.

Preserve uncertainty. Sparse/conflicting evidence remains sparse/conflicting.

## Deep inspection

Only when the user explicitly asks for a forensic breakdown, exact measurements, motion details, or implementation analysis, read `references/deep-capture.md`.

For tool semantics/debugging, read `references/tool-contract.md`.

For example fingerprint fields, read `references/style-fingerprints.md`.

The default path is **capture richly server-side, return compactly, retrieve compactly**.
