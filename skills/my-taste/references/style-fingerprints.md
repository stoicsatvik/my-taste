# Style fingerprint schemas

These are extraction guides, not rigid database schemas. Include only features actually supported by the inspected artifact. Do not hallucinate missing values.

## Writing

Recommended fields:

```json
{
  "tone": "direct",
  "sentence_length": "short-medium",
  "rhythm": "variable",
  "specificity": "high",
  "abstraction": "medium",
  "vocabulary": "conversational-precise",
  "humor": "dry-sparse",
  "adjective_density": "low",
  "first_person": "occasional",
  "structure": ["claim", "example", "sharp-close"],
  "opening_style": "immediate",
  "ending_style": "compressed",
  "corporate_language": "low"
}
```

Useful context:
- `format`: essay, caption, cold_email, landing_page_copy, script
- `audience`
- `purpose`
- `channel`

Do not store the article's factual claims as style features.

## Website / UI

Recommended fields:

```json
{
  "layout": "asymmetric-editorial",
  "density": "low",
  "whitespace": "high",
  "hierarchy": "strong",
  "typography": ["large-display-sans", "compact-body"],
  "palette": ["neutral-base", "single-accent"],
  "contrast": "high",
  "border_radius": "medium",
  "borders": "subtle",
  "shadows": "minimal",
  "cards": "restrained",
  "navigation": "minimal",
  "imagery": "large-purposeful",
  "motion": "restrained",
  "button_style": "simple-solid",
  "information_density": "progressive-disclosure"
}
```

Useful context:
- `surface`: landing_page, dashboard, ecommerce, portfolio, mobile_app
- `product_type`
- `industry`
- `device`
- `goal`

Prefer describing the design grammar over naming fashionable labels such as "Apple-like" unless the label genuinely adds information.

## Video

Inspect multiple points in time when possible.

Recommended fields:

```json
{
  "hook": "immediate-visual",
  "pacing": "fast",
  "average_shot_length": "short",
  "cuts_per_minute": 18,
  "narrative_structure": ["hook", "escalation", "payoff"],
  "camera_motion": "restrained",
  "framing": "tight",
  "b_roll": "selective",
  "transitions": "mostly-hard-cuts",
  "caption_density": "low",
  "caption_style": "minimal",
  "on_screen_text": "sparse",
  "color_grade": "natural-high-contrast",
  "lighting": "available-light",
  "music_energy": "medium-high",
  "audio_editing": "beat-aware",
  "sound_effects": "sparse",
  "voiceover": "none",
  "retention_mechanics": ["pattern-interrupt", "visual-payoff"],
  "ending": "hard-stop"
}
```

Useful context:
- `platform`: instagram, youtube, tiktok, film
- `format`: reel, short, longform, ad, vlog, montage
- `genre`
- `duration_class`
- `goal`: retention, explanation, emotion, conversion

If audio cannot be inspected, omit audio features. If only a transcript is available, do not invent camera or editing features. If only a thumbnail is available, do not save a full video fingerprint.

## Positive and negative evidence

Positive evidence answers:
> What should future outputs borrow when the context matches?

Negative evidence answers:
> What should future outputs avoid when the context matches?

Store both with the same feature vocabulary whenever possible so `rank_profiles` can compare them directly.
