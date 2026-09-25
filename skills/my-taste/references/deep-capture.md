# Deep reference capture

When the user says to save, learn, copy, remember, or analyze a visual/video style, default to **deep capture**, not a seven-bullet vibe summary.

Deep does **not** mean verbose model context. Capture richly, compress server-side, and return only the minimum receipt needed to continue.

The goal is to preserve enough evidence that a future agent can reproduce the design grammar without copying protected assets or pretending to have observed unavailable states.

## Fidelity levels

Record the strongest fidelity actually available:

- `static_raster`: screenshot/image only.
- `multi_state_raster`: several screenshots/states or breakpoints.
- `live_visual`: a live page can be browsed and interacted with.
- `dom_css`: DOM/computed styles/CSS variables are inspectable.
- `motion_timeline`: animation or video can be observed over time.
- `source_code`: implementation files are available.

Never upgrade the fidelity label by inference.

## Static screenshot capture

A screenshot can support a detailed **static** fingerprint. Capture, when observable:

### Pixel evidence

If a local file path is available, call `analyze_image_file` and include its deterministic evidence:

- exact raster width/height/aspect ratio,
- SHA-256 provenance hash,
- dominant colors and approximate pixel fractions,
- light/dark area fractions,
- saturation/luminance statistics,
- edge-density proxy.

This is the literal pixel-derived layer. Do not call it semantic understanding.

### Geometry

Estimate normalized or pixel-relative geometry for the important visible regions:

- viewport margins,
- hero height,
- content max-width,
- column ratios,
- gutters,
- card dimensions,
- alignment anchors,
- whitespace bands,
- overlap/layer relationships,
- repeated spacing increments.

Prefer concrete measurements or ranges over words like "spacious".

### Typography

Capture what is visible:

- apparent family/category; exact family only when known,
- display/body size estimates,
- weight,
- line-height,
- letter-spacing,
- casing,
- measure/line length,
- hierarchy ratios,
- contrast between display and body styles.

### Surface system

Capture:

- exact/estimated palette roles,
- borders/stroke widths,
- radii by component type,
- shadow blur/spread/opacity character,
- background treatment,
- gradients/textures,
- card elevation,
- icon style,
- image/illustration treatment,
- button dimensions and visual states if visible.

### Composition and component grammar

Capture:

- grid and alignment logic,
- component density,
- navigation structure,
- CTA placement,
- visual focal points,
- screenshot/product-frame treatment,
- section rhythm,
- repetition/variation patterns,
- progressive disclosure.

### What a screenshot cannot prove

Set these as unobserved rather than guessing:

- hover/focus/pressed states,
- transition duration/easing,
- scroll-triggered effects,
- parallax,
- page-load sequences,
- cursor-follow effects,
- responsive reflow outside the shown breakpoint,
- animation choreography.

A static screenshot contains no time axis. Do not fabricate one.

## Live website capture

When the user supplies a live URL and browsing/interacting is available, inspect more than the hero.

Capture representative states across:

- initial load,
- first viewport,
- at least 2-4 lower sections,
- nav behavior,
- hover/focus states where meaningful,
- scroll progress,
- modal/menu states when present,
- mobile/tablet/desktop breakpoints when available.

If DOM/CSS inspection is possible, prefer exact values for:

- CSS variables/tokens,
- font families,
- font sizes/weights/line heights,
- max-widths,
- gaps/padding/margins,
- radii,
- shadows,
- colors,
- breakpoints,
- transition properties,
- animation names/durations/easing/delays,
- transform/opacity/filter changes.

For motion, record a timeline rather than "smooth animation":

```json
{
  "trigger": "page_load",
  "target": "hero_heading",
  "property": ["opacity", "translateY"],
  "from": {"opacity": 0, "translateY_px": 18},
  "to": {"opacity": 1, "translateY_px": 0},
  "duration_ms": 520,
  "delay_ms": 80,
  "easing": "cubic-bezier(...)",
  "stagger_ms": 60,
  "evidence": "observed|computed_css|estimated"
}
```

If exact timing cannot be measured, use a range and label it estimated.

## Video / screen-recording capture

Sample multiple points over time. For short-form video, inspect enough of the timeline to cover opening, middle, and ending.

Capture:

- duration, aspect ratio, frame-rate when measurable,
- hook onset time,
- shot boundaries and approximate shot lengths,
- cuts/minute,
- transition types,
- text/caption entry/exit behavior,
- camera motion,
- zoom/punch-in frequency,
- B-roll cadence,
- rhythm relative to speech/music,
- color/lighting changes,
- sound effects,
- music energy,
- retention devices,
- ending/payoff structure.

For UI screen recordings, additionally capture interaction choreography: cursor/gesture → state change → timing → easing → destination.

## Storage shape

Store deep analysis as nested `features`; My Taste supports nested feature comparison.

Recommended top-level groups:

```json
{
  "capture": {},
  "geometry": {},
  "typography": {},
  "palette": {},
  "surface": {},
  "components": {},
  "composition": {},
  "interaction": {},
  "motion": {},
  "responsive": {},
  "content_style": {},
  "distinctive_signatures": []
}
```

Omit groups that are not observable instead of filling them with guesses.

## Applying a deep reference

A future task should retrieve the context-specific taste brief, then use individual evidence when exact reference details matter.

Borrow **design grammar**, not protected logos, illustrations, copy, or exact page composition.

When evidence came from a static screenshot, do not invent matching animation behavior merely because the visual style matches.


## Context-cost rule

For live website references, the preferred path is:

```text
save_website_reference
  -> browser/DOM/CSS/motion capture inside MCP process
  -> compact forensic fingerprint in SQLite
  -> full raw capture gzip sidecar on local disk
  -> tiny receipt back to the model
```

Do not send the full element/style/animation dump to the model and then ask it to compress the dump. That spends tokens without improving the stored evidence.

For screenshot references, prefer `save_image_reference` when a local path exists. Add only a compact semantic feature object from host vision.

Ordinary future generation should use compact `taste_brief`, usually 4-6 rules. Retrieve raw evidence only for provenance or exact forensic follow-up.
