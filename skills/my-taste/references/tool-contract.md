# My Taste MCP tool contract

The MCP server is the durable preference layer. The Agent Skill decides when to call these tools.

## `observe_artifact`

Store an explicitly liked or disliked structured style fingerprint.

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

The perception step belongs to the calling agent. My Taste stores the derived evidence and does not pretend it independently watched a video or browsed a website.

## `retrieve_taste`

Retrieve the most relevant evidence for the current context.

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

The returned evidence includes provenance and relevance. Relevance is a retrieval score, not a calibrated probability that the user will approve the final output.

## `rank_profiles`

Rank structured candidate fingerprints against relevant positive and negative taste evidence.

Inputs:
- `candidates: [{id?, label?, features}]`
- `domain: str`
- `context: object | null`
- `modality: str = ""`

Use after candidate outputs have been converted into comparable style fingerprints.

A higher score means "more consistent with retrieved evidence," not "objectively better."

## `observe_choice`

Strong pairwise text evidence.

Inputs:
- `preferred: str`
- `rejected: str`
- `domain: str = "writing"`
- `context: str = ""`

Semantics: `preferred > rejected`.

## `observe_edit`

Strong text evidence from a known rewrite.

Inputs:
- `original: str`
- `edited: str`
- `domain: str = "writing"`
- `context: str = ""`

Semantics: `edited > original`.

## `rank_text`

Legacy/interpretable lexical ranking for raw text candidates.

This uses learned lexical feature weights and is complementary to structured style evidence.

## `taste_profile`

Returns the strongest learned lexical preference weights for a domain.

This is v0.1's interpretable text model, not the complete multimodal profile.

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
