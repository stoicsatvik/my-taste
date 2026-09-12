# My Taste — Unified Foundry State

## Mission
Build a local-first, user-owned multimodal preference layer that predicts pairwise choice and exposes learned taste to authorized AI agents through MCP.

Core objective: `P(candidate_i > candidate_j | user, domain, context, evidence, history)`.

## Durable claim state
- Frozen v0.1 text baseline: **SUPPORTED** repository baseline.
- V0.2 context/provenance integration behavior: **SUPPORTED**.
- Cumulative contextual drift topology: **REJECTED** on its frozen synthetic drift gate.
- Bounded-recency global+context topology: **REJECTED**: local reversal adapted but contaminated an unrelated context through global updates.
- Exact-context isolation topology: **SUPPORTED** for local reversal/invariance, but **REJECTED as a complete V0.2 architecture** because `synthetic-related-context-transfer-v1` produced zero transfer to the related unseen context.
- Hierarchical explicit-family challenger: **NOT YET PROVEN** pending exact-head CI on PR #9.
- Real-user contextual generalization, multimodal gains, and real MCP-client interoperability: **NOT YET PROVEN**.

## Current challenger — explicit family hierarchy
Branch: `foundry/v0.2-hierarchical-context-challenger`.
Base: rejected exact-context transfer head `512554724af224e7353cbe1af786e4dcf6287ae3`.
PR: #9 (draft; never merge without explicit approval).

Architecture: contextual evidence is prohibited from mutating domain-global weights. Caller-supplied context families provide a bounded middle layer: `global -> explicit family residual -> exact context residual`. The frozen `family_share` is 0.35; no semantic family inference is claimed.

Frozen gate `synthetic-hierarchical-transfer-v1`:
- 8 observations in `work-email`;
- `work-email` and unseen `work-memo` are explicitly assigned to family `work`;
- `casual-chat` is explicitly assigned to family `casual`;
- trained and related-unseen preference probability must each reach >= 0.60;
- after 8 local reversals, reversed trained-context probability must reach >= 0.60;
- unrelated-context drift must remain <= 1e-12 after both training and reversal.

The failed exact-context transfer gate remains in CI with `continue-on-error: true` so the negative result is preserved. Thresholds and family share must not be tuned after inspecting CI; a failure requires a separately versioned challenger.

## Privacy / safety boundary
Public fixtures are synthetic. Never commit private messages, screenshots, credentials, sensitive exports, identifying datasets, or real private preference evidence. Context families in the current benchmark are explicit test metadata, not inferred user traits.

## Current blockers / unknowns
- Exact-head CI for PR #9 has not yet established whether bounded family sharing satisfies transfer + isolation + reversal simultaneously.
- No real/consented external preference benchmark.
- No screenshot/image benchmark foundation yet.
- MCP integration still lacks real compatible-client interoperability validation.

## Next best move
Observe exact-head PR #9 CI without changing thresholds. If it passes, attack family misassignment and cross-family leakage under a sealed fixture before promotion. If it fails, preserve the failure and diagnose which of transfer, isolation, or reversal adaptation broke rather than tuning the holdout.
