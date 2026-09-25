# My Taste

**A local-first, user-owned contextual preference layer for AI agents.**

My Taste learns what a person would choose from explicit evidence, stores reusable style fingerprints with context and provenance, and exposes the result to AI agents through MCP.

The core question is:

> **Given this task and everything the user has explicitly liked or rejected before, what should the agent borrow, avoid, or rank higher?**

Long-term objective:

```text
P(candidate_i > candidate_j | user, domain, context, evidence, history)
```

## What works now

My Taste currently has two complementary preference systems.

### 1. Pairwise text learning

For explicit text choices and edits:

```text
preferred > rejected
edited > original
```

The interpretable baseline extracts lexical features and updates an online Bradley-Terry/logistic-style model.

### 2. Contextual artifact taste

For a single liked or disliked reference, an agent can inspect the artifact and save a structured fingerprint:

```text
TasteEvidence(
  domain,
  modality,
  context,
  features,
  preference,
  strength,
  provenance
)
```

This now supports the workflow for:

- **writing references**
- **websites and UI screenshots**
- **videos and editing references**
- future modalities that can be represented as structured features

The important architectural boundary is deliberate:

```text
browser / vision / video-capable agent
          |
          | inspect reference
          v
structured style fingerprint
          |
          v
My Taste
  - durable evidence
  - context matching
  - provenance
  - positive / negative preferences
  - profile ranking
          |
          v
future agent task
```

My Taste does not pretend its SQLite process independently watched a video. The calling agent performs perception; My Taste owns preference memory and retrieval.

## Example: save a website style

An agent inspecting a liked SaaS landing page might store:

```json
{
  "domain": "ui_design",
  "modality": "website",
  "context": {
    "surface": "landing_page",
    "industry": "saas",
    "goal": "conversion"
  },
  "features": {
    "density": "low",
    "whitespace": "high",
    "hierarchy": "strong",
    "palette": ["neutral-base", "single-accent"],
    "shadows": "minimal",
    "motion": "restrained"
  },
  "preference": "positive"
}
```

Later, when the user asks for another SaaS landing page, the Agent Skill retrieves the most relevant `ui_design` evidence automatically.

## Example: save a writing style

A liked writing sample can be stored without needing a rejected comparison:

```json
{
  "domain": "writing",
  "modality": "text",
  "context": {
    "format": "landing_page_copy",
    "audience": "founder"
  },
  "features": {
    "tone": "direct",
    "sentence_length": "short-medium",
    "specificity": "high",
    "humor": "dry-sparse",
    "corporate_language": "low"
  }
}
```

Pairwise choices and edits remain stronger signals where available.

## Example: save a video style

A video-capable agent can sample a liked Reel and store:

```json
{
  "domain": "video",
  "modality": "video",
  "context": {
    "platform": "instagram",
    "format": "reel",
    "goal": "retention"
  },
  "features": {
    "hook": "immediate-visual",
    "pacing": "fast",
    "cuts_per_minute": 18,
    "camera_motion": "restrained",
    "transitions": "mostly-hard-cuts",
    "caption_density": "low",
    "music_energy": "medium-high",
    "ending": "hard-stop"
  }
}
```

Future Reel tasks can retrieve this. A long documentary task should not blindly inherit it because context is part of the evidence.

## One-line Codex install

In Codex with Full access, run:

```bash
codex plugin marketplace add stoicsatvik/my-taste
```

This repository is itself a Codex Git marketplace. Its single `my-taste` plugin is marked `INSTALLED_BY_DEFAULT` and bundles:

- the My Taste skill,
- a local stdio MCP server,
- a first-run isolated Python runtime,
- persistent preference data at `~/.my_taste/taste.db`.

The first MCP launch installs Python dependencies into `~/.my_taste/codex-runtime`; protocol output remains clean because setup logs are sent to stderr. Start a new Codex chat after installation so the plugin and skill are loaded.

## Try it with ChatGPT

For a temporary local-first test, install/update My Taste from this repository, start the MCP server, and expose it through a verified Cloudflare Quick Tunnel with one command:

```bash
curl -fsSL https://raw.githubusercontent.com/stoicsatvik/my-taste/main/bootstrap.py | python3
```

The bootstrap:

1. creates an isolated runtime under `~/.my_taste/runtime`,
2. installs the current GitHub source archive,
3. keeps preference data in `~/.my_taste/taste.db`,
4. downloads `cloudflared` from the official Cloudflare GitHub release only when needed and verifies its SHA-256 checksum,
5. starts My Taste over Streamable HTTP,
6. prints a temporary public `https://...trycloudflare.com/mcp` URL.

Keep that terminal open during the test.

Then in ChatGPT, enable Developer mode, create a personal MCP plugin using the printed `/mcp` URL, and use it in a chat. ChatGPT currently connects personal MCP plugins by endpoint URL rather than directly installing a GitHub repository URL.

### Screenshot -> saved UI taste -> landing page

1. Attach a screenshot and say:

   `I like this website UI. Analyze its visual grammar and save it to My Taste.`

2. The host model should inspect the screenshot and call `observe_artifact` with `domain="ui_design"`, `modality="screenshot"`, context tags, and derived visual features.

3. In a later taste-sensitive request, say:

   `Create a SaaS landing page for an AI operations product.`

4. My Taste should call `taste_brief` for the inferred landing-page context before the design is finalized. Relevant saved positive features should be applied, negative features avoided, and unrelated dashboard/video/writing evidence should not leak in.

### Video reference -> later video task

Attach a video or otherwise provide a video the host can actually inspect, then say:

`I like this editing style. Save it to My Taste.`

The host should sample multiple moments when available and save a video fingerprint covering pacing, hooks, cuts, captions, camera behavior, transitions, color/lighting, audio behavior, retention mechanics, and ending style. A later matching Reel/Short task should retrieve that video taste automatically through `taste_brief`.

## Install

```bash
pip install -e ".[dev]"
```

The default database is `~/.my_taste/taste.db`.

Override it with:

```bash
export MY_TASTE_DB=/path/to/taste.db
```

## CLI

Text pairwise learning:

```bash
my-taste observe-choice \
  --preferred "Your website should make the offer obvious in five seconds." \
  --rejected "Transform your digital presence with next-generation solutions."
```

Save a structured artifact fingerprint:

```bash
my-taste observe-artifact \
  --domain ui_design \
  --modality website \
  --context-json '{"surface":"landing_page","industry":"saas"}' \
  --features-json '{"density":"low","whitespace":"high","shadows":"minimal"}'
```

Retrieve context-relevant evidence:

```bash
my-taste retrieve \
  --domain ui_design \
  --modality website \
  --context-json '{"surface":"landing_page","industry":"saas"}'
```

## MCP

Run locally over stdio:

```bash
my-taste-mcp
```

or during development:

```bash
mcp dev src/my_taste/mcp_server.py
```

For Streamable HTTP:

```bash
MY_TASTE_MCP_TRANSPORT=streamable-http my-taste-mcp
```

Default endpoint:

```text
http://127.0.0.1:8000/mcp
```

### MCP tools

- `observe_choice`
- `observe_edit`
- `observe_artifact`
- `retrieve_taste`
- `taste_brief`
- `rank_profiles`
- `rank_text`
- `taste_profile`
- `explain_text`

## Agent Skill

The repository includes an Agent Skills-compatible package:

```text
skills/my-taste/
├── SKILL.md
└── references/
    ├── tool-contract.md
    └── style-fingerprints.md
```

The skill teaches agents to:

- recognize explicit "I like this / save this style" signals,
- inspect websites, text, screenshots, and videos using available perception tools,
- store compact reusable fingerprints,
- retrieve relevant taste automatically for normal future creative tasks,
- avoid applying unrelated evidence across domains or contexts,
- rank structured candidates against positive and negative evidence.

Build the uploadable skill bundle:

```bash
python scripts/package_skill.py
```

Build the portable Agent Plugin package:

```bash
python scripts/package_plugin.py
```

Outputs:

```text
dist/my-taste-skill.zip
dist/my-taste-plugin.zip
```

The repository root also contains `plugin.json`, the portable Agent Plugins manifest. The temporary ChatGPT MCP test still requires registering the printed HTTPS endpoint because the tunnel URL is created at runtime.

## Architecture

```text
Explicit preference
      |
      +-- pairwise text choice / edit
      |
      +-- liked/disliked artifact
              |
              v
       agent perception
              |
              v
     structured fingerprint
              |
              v
      SQLite evidence store
              |
       context retrieval
              |
      +-------+--------+
      |                |
  rank raw text   rank profiles
      |                |
      +-------+--------+
              v
        MCP + Skill
              |
              v
        future agents
```

## Design principles

- **Local first**: private raw evidence should not require a cloud service.
- **User owned**: storage and exports should remain portable.
- **Evidence backed**: learned preferences retain provenance.
- **Contextual**: landing-page taste is not automatically dashboard taste.
- **Multimodal without lock-in**: perception adapters can change while the evidence contract survives.
- **Uncertain by default**: weak evidence stays weak.
- **Scoped access**: agents should retrieve only the taste domain they need.
- **Copyright-conscious**: store reusable abstractions rather than unnecessary copies of source material.

## Current limits

This is not yet a fully local computer-vision/video-analysis stack.

For websites, screenshots, and videos, the current production path is:

```text
capable agent inspects -> My Taste stores/retrieves
```

Direct local frame extraction, scene segmentation, audio analysis, perceptual hashing, embeddings, contradiction handling, and calibrated TasteBench evaluation remain work in progress.

## Roadmap

See [`ROADMAP.md`](ROADMAP.md).

## License

MIT
