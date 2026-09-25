# My Taste MCP tool contract

## Low-token primary path

### `save_website_reference`

Preferred tool for an explicit liked/disliked **live website**.

It performs, inside the MCP process:

```text
browser capture
-> DOM/CSS/pixel/motion forensic data
-> compact fingerprint
-> taste evidence save
-> gzip raw sidecar
-> tiny receipt
```

The raw element/style/animation dump is not returned to the model.

Inputs include:
- `url`
- compact `context`
- `preference`
- `strength`
- optional compact `semantic_features`

### `save_image_reference`

Preferred tool for an explicit liked/disliked local screenshot/image when a readable path exists.

Pixel evidence is calculated server-side and saved with optional compact host-derived semantic features. Motion/interaction remain unobserved for a still image.

### `taste_brief`

Preferred retrieval tool for ordinary generation. It is compact by default and returns only feature, value, and confidence for a small number of `prefer`, `avoid`, and conflict rules.

Use `verbose=true` only when support/provenance details materially matter.

### `analyze_website`

Returns a **compact forensic fingerprint**, not the raw browser dump.

Use only when the user explicitly asks to inspect/explain the analysis. For saving, use `save_website_reference` instead.

---


The MCP server is the durable preference layer. The Agent Skill decides when to call these tools. The server also advertises core workflow instructions so the save/retrieve loop still works during direct MCP testing.

## `observe_artifact`

Persist an explicitly liked or disliked structured style fingerprint **after the calling agent has actually inspected the reference**.

Inputs:
- `domain: str`
- `modality: str`
- `features: object`
- `context: object | null`
- `preference: "positive" | "negative"`
- `strength: float = 1.0`
- `source_reference: str = ""`
- `note: str = ""`

Use this for:
- a liked website or screenshot,
- a liked writing sample with no comparison,
- a liked/disliked video,
- future modalities represented by structured fingerprints.

The perception step belongs to the calling agent. My Taste stores the derived evidence and does not pretend it independently watched a video, read an unattached image, or browsed a website.

## `taste_brief`

Preferred tool before generating taste-sensitive output.

Inputs:
- `domain: str`
- `context: object | null`
- `modality: str = ""`
- `limit: int = 12`

Returns:
- `prefer`: context-relevant positive feature/value guidance,
- `avoid`: context-relevant negative feature/value guidance,
- `conflicts`: features with both positive and negative support,
- `confidence`,
- `evidence_count`.

Apply high-confidence guidance, avoid forcing conflicts, and fall back to explicit user instructions when evidence is weak.

## `retrieve_taste`

Retrieve individual context-relevant evidence when provenance or the original fingerprints are useful.

Inputs:
- `domain: str`
- `context: object | null`
- `modality: str = ""`
- `limit: int = 8`

Ranking combines:
- exact domain,
- contextual similarity,
- modality match,
- evidence strength,
- mild recency.

Relevance is a retrieval score, not a calibrated probability that the user will approve the final output.

## `rank_profiles`

Rank structured candidate fingerprints against relevant positive and negative taste evidence.

Inputs:
- `candidates: [{id?, label?, features}]`
- `domain: str`
- `context: object | null`
- `modality: str = ""`

Use after candidate outputs have been converted into comparable style fingerprints.

## `observe_choice`

Strong pairwise text evidence.

Semantics: `preferred > rejected`.

## `observe_edit`

Strong text evidence from a known rewrite.

Semantics: `edited > original`.

## `rank_text`

Interpretable lexical ranking for raw text candidates.

## `taste_profile`

Returns the strongest learned lexical preference weights for a domain.

## `explain_text`

Explains the lexical contribution of a raw text candidate.

## Evidence hierarchy

Strongest:
1. repeated explicit pairwise choices,
2. direct edits,
3. explicit liked/disliked artifacts with rich inspected fingerprints,
4. explicit single-reference style saves with sparse fingerprints.

Not evidence:
- silence,
- demographic inference,
- assistant speculation,
- unrelated memories,
- an output merely being generated,
- one domain being projected into another without instruction.

## Privacy and copyright boundary

Store preference abstractions and minimal provenance by default.

Do not use My Taste as a warehouse for complete copyrighted articles, videos, transcripts, image sets, or cloned websites. The useful object is the preference fingerprint, not an unnecessary copy of the source material.
