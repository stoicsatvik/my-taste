---
name: my-taste
description: Learn, retrieve, and apply the user's evidence-backed taste across writing, websites/UI, video, and other structured modalities. Use when the user says they like/dislike a reference, asks to save/copy/learn a style, asks which candidate fits their taste, or requests a taste-sensitive output such as writing, UI/design, branding, or video. For normal taste-sensitive generation, retrieve relevant My Taste evidence automatically when available. Persist taste only through My Taste MCP tools; never invent learned preferences from stereotypes or unrelated memory.
---

# My Taste

Use My Taste as a **contextual preference layer**, not a personality profile.

The system models:

`P(candidate_i > candidate_j | user, domain, context, evidence, history)`

The Skill decides **when to observe, retrieve, rank, and apply**. The MCP server owns durable evidence and learned state.

Read:
- `references/tool-contract.md` for tool semantics.
- `references/style-fingerprints.md` for compact fingerprints.
- `references/deep-capture.md` whenever the user asks to save, learn, copy, remember, or deeply analyze a screenshot, website, UI, or video style.

## Core rules

1. **Explicit task requirements outrank taste.**
   Correctness, safety, factual constraints, and direct user instructions come first.

2. **Retrieve automatically when taste is relevant.**
   For writing, UI/design, branding, video/editing, and similar creative choices, infer a compact task context and call `retrieve_taste` before finalizing when My Taste is available. The user should not have to repeat "use my taste."

3. **Context is part of the preference.**
   A preference saved for an Instagram Reel should not automatically control a documentary. Landing-page preferences should not silently control dense admin dashboards. Retrieve by domain plus context.

4. **Do not generalize across domains.**
   Writing evidence is not UI evidence. UI evidence is not video evidence. Cross-domain inspiration is allowed only when the user explicitly asks for it.

5. **Persist only real preference evidence.**
   Strong signals include:
   - explicit "I like this" / "save this style",
   - explicit dislike,
   - A > B choices,
   - direct user edits where original and edited forms are known.

   Silence, mere completion, demographic assumptions, assistant guesses, and unreviewed outputs are not evidence.

6. **Store derived fingerprints, not unnecessary raw content.**
   Keep provenance such as a URL or user-visible reference when useful, but prefer compact structured style features over copying full copyrighted text, full video transcripts, or entire webpage contents into taste storage.

7. **Preserve uncertainty.**
   Sparse or conflicting evidence should remain sparse or conflicting. Do not manufacture a single universal aesthetic.

## Automatic context routing

Before a taste-sensitive task, derive a compact context such as:

```json
{
  "surface": "landing_page",
  "industry": "saas",
  "goal": "conversion"
}
```

or:

```json
{
  "platform": "instagram",
  "format": "reel",
  "goal": "retention"
}
```

Then retrieve the relevant domain:

- prose, captions, scripts, messages, copy -> `writing`
- websites, app screens, dashboards, visual systems -> `ui_design`
- editing, reels, short films, video composition -> `video`

Use a modality hint when useful:
- `text`
- `website`
- `screenshot`
- `video`

## Token discipline

Preserve forensic detail **locally**, not in the model transcript.

- For an explicit live-website save, prefer `save_website_reference`. It performs capture + compaction + persistence server-side and returns only a receipt.
- For a local screenshot/image save, prefer `save_image_reference` with a compact semantic fingerprint. Do not call `analyze_image_file` first unless the user explicitly asks to see the analysis.
- Use `analyze_website` only when the user asks to inspect/show/explain the website analysis itself.
- Use compact `taste_brief` for ordinary generation. Do not call `retrieve_taste` unless individual provenance/reference details are actually required.
- Do not echo the full stored fingerprint back to the user after saving. Confirm the category, fidelity, and a few signatures.
- Large raw website captures are intentionally stored as compressed local sidecars instead of being injected into model context.

## Learn a reference

When the user says things like:

- "I like this website. Save the style."
- "Copy the feel of this UI and remember it."
- "I like how this text is written."
- "Remember this Reel's editing style."
- "Never use this kind of design again."

follow this workflow:

1. **Inspect the actual reference** using the available browser, image, file, or video capabilities.
2. **Use deep capture by default.** Read `references/deep-capture.md`. A short aesthetic summary is not enough when the user says to save the reference.
3. **Choose the cheapest correct save path:**
   - live public URL -> `save_website_reference`;
   - local screenshot/image path -> `save_image_reference`;
   - text/video/other reference -> compact host fingerprint + `observe_artifact`.
4. **Separate content from style.** Extract reusable choices, not topic-specific facts.
5. **Record observability honestly.** A static screenshot cannot prove animations, hover states, scroll effects, responsive behavior outside the shown viewport, or interaction timing.
6. **Infer context** from the artifact and user's instruction.
7. Only use separate analysis + `observe_artifact` when the one-shot save tools cannot represent the reference.
   - domain,
   - modality,
   - fingerprint features,
   - compact context,
   - `positive` or `negative`,
   - source reference when useful.
8. Confirm what category and fidelity of taste was saved without dumping the full forensic fingerprint unless the user asks.

If the artifact cannot actually be inspected, do not fabricate a fingerprint. State that the reference was not analyzable and avoid saving invented evidence.

## Website / UI references

When a website or UI is explicitly liked/disliked:

1. For a static screenshot, capture pixel evidence, geometry, typography, surface system, components, composition, and distinctive signatures at the highest observable precision. When saving, prefer `save_image_reference` so pixel analysis remains server-side.
2. For a live public URL being **saved**, call `save_website_reference` when available. It captures rendered pixels, DOM geometry, computed styles, CSS tokens, breakpoints, and Web Animations evidence server-side while returning only a compact receipt. Call `analyze_website` only when the user explicitly wants the forensic analysis surfaced in the conversation.
3. Inspect representative sections and states, not only the hero. When browser interaction is available, additionally inspect hover/focus/menu/modal states that the automated capture did not trigger.
4. Never infer motion from a still image. If motion matters and only a screenshot is available, save the static design faithfully and mark motion as unobserved.
5. Save under `domain="ui_design"`.
6. Use `modality="website"` for live pages and `modality="screenshot"` for static captures.
7. Include context such as surface, product type, industry, device, goal, and capture fidelity when inferable.

Do not save the site's brand identity or exact copyrighted assets as if they were reusable style rules. Capture the design grammar.

## Writing-style references

When the user likes a single piece of writing, `observe_choice` is insufficient because there is no rejected comparison.

Instead:

1. Analyze the sample's style fingerprint.
2. Save it using `observe_artifact(domain="writing", modality="text", ...)`.
3. Include context such as format, audience, purpose, and channel.

Pairwise choices and edits should still use `observe_choice` / `observe_edit` because they provide stronger comparative evidence.

## Video references

When the user likes/dislikes a video:

1. Inspect as much of the actual video as available and sample multiple points across the timeline.
2. Read `references/deep-capture.md` and capture measurable timing/shot/transition evidence when the host can observe it.
3. Separate:
   - narrative structure,
   - editing rhythm,
   - visual composition,
   - captions/text treatment,
   - camera behavior,
   - transitions,
   - color/lighting,
   - music/audio behavior,
   - hook and retention mechanics.
3. Sample multiple moments across the video. Do not infer the whole style from one thumbnail.
4. Save a structured fingerprint using:
   - `domain="video"`
   - `modality="video"`
5. Include context such as platform, format, genre, duration class, and goal.
6. Do not store full copyrighted transcripts, frames, or audio unless the user explicitly needs a local reference workflow. Prefer derived features and provenance.

## Apply taste automatically

When generating a taste-sensitive output:

1. Determine domain and task context.
2. Call compact `taste_brief` for the task context. Use `retrieve_taste` only when provenance or individual references are needed.
3. Apply the brief's high-confidence `prefer` guidance, avoid its `avoid` guidance, and do not force features listed as conflicts.
4. Generate the output.
5. If there are multiple structured candidates and ranking matters, fingerprint each candidate and call `rank_profiles`.
6. For raw writing candidates, the existing lexical `rank_text` may be used as an additional signal.
7. Do not mention My Taste unless it materially helps the user understand the result.

The preferred behavior is silent contextual application, not forcing the user to invoke `@MyTaste` every time. When the brief has low confidence or no evidence, fall back to the user's explicit request instead of pretending personalization is strong.

## Pairwise and edit learning

For explicit text A > B:

`observe_choice(preferred, rejected, domain, context)`

For a known user rewrite:

`observe_edit(original, edited, domain, context)`

These update the interpretable online text ranker and remain stronger than an isolated style reference.

## Failure behavior

If tools are unavailable, evidence is empty, or the requested domain is unsupported:

- complete the underlying task using explicit instructions,
- do not claim stored taste was applied,
- do not create fictional preference evidence.

Prefer narrow, evidence-backed personalization over personalized fan fiction.
