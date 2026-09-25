# My Taste MCP tool contract

This reference describes how the current My Taste skill should use the repository's MCP surface.

## Tools

### `observe_choice`

Use for explicit pairwise preference evidence.

Inputs:
- `preferred: str`
- `rejected: str`
- `domain: str = "writing"`
- `context: str = ""`

Semantics: records `preferred > rejected` and updates the online preference model.

Do not call when the user's preference is ambiguous.

### `observe_edit`

Use when the user edits a known original and the edit itself is a preference signal.

Inputs:
- `original: str`
- `edited: str`
- `domain: str = "writing"`
- `context: str = ""`

Semantics: records `edited > original`.

### `rank_text`

Use to rank viable text candidates according to learned weights.

Inputs:
- `candidates: list[str]`
- `domain: str = "writing"`

Returns candidates sorted by model score with strongest feature contributions.

A higher score means "more consistent with the current learned model," not "objectively better."

### `taste_profile`

Use to inspect the strongest learned feature weights for a domain.

Inputs:
- `domain: str = "writing"`
- `limit: int = 20`

Returns feature, direction, weight, evidence-count confidence, update count, and update timestamp.

Confidence is evidence-count based in v0.1. It is not a calibrated probability that a psychological statement is true.

### `explain_text`

Use to explain how one text candidate interacts with the learned weights.

Inputs:
- `text: str`
- `domain: str = "writing"`

Returns the score, extracted features, and strongest positive/negative contributions.

## v0.1 model limitations

The current extractor uses a compact interpretable lexical feature set. It can learn signals including brevity, specificity, corporate-language density, intensity, person references, questioning, structured formatting, uppercase emphasis, lexical variety, and sentence length.

It does **not** yet understand the full semantic, aesthetic, contextual, visual, or multimodal structure of human taste.

Therefore:

- preserve uncertainty,
- never imply the feature model is a complete representation of the user,
- never generalize writing weights into unrelated domains,
- prefer held-out evaluation over anecdotes,
- keep evidence provenance intact,
- do not commit private evidence or the local SQLite database to the public repository.

## Evidence hierarchy

Strong:
1. explicit A > B choice,
2. direct user edit where original and edited text are known.

Not evidence in v0.1:
- assistant speculation,
- silence,
- message sentiment alone,
- demographic inference,
- unrelated memories,
- an unreviewed assistant output,
- preferences inferred across domains.

## Architectural boundary

The Skill defines **when and how** to use My Taste.

The MCP server defines **live tools and controlled actions**.

SQLite stores **private evidence and learned weights**.

The public repository defines **code, protocol, tests, and synthetic fixtures**, not the user's private preference corpus.
