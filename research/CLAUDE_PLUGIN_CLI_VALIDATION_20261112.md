# Claude Code plugin CLI validation — 2026-11-12

Branch: `foundry/claude-plugin-cli-validation-20261112`  
Base: `main`  
Pinned CLI: `@anthropic-ai/claude-code@2.1.322` (official GitHub release published 2026-11-10).

## Why this test exists

The repository already has static package checks for the Claude plugin manifest, Codex plugin manifest, MCP entry points, hook paths, skill bundle and distributable ZIP. Those checks do not prove that the actual Claude Code CLI accepts the plugin package.

This isolated workflow installs the pinned official CLI and runs:

```sh
claude plugin validate . --strict
```

No API key, account token, paid API, or model invocation is configured. Automatic updates and nonessential CLI traffic are disabled. The test is a local package/manifest validation, not an authenticated Claude session or a guarantee that every client version loads the plugin.

## Evidence boundary

- Existing Python/package tests remain the baseline for skill resource completeness, MCP tool registration and distributable contents.
- This workflow adds actual CLI parser/validator coverage.
- It does not prove remote MCP interoperability or that a live Claude session invokes the hooks as intended.
- Codex's existing package checks remain separate; this does not claim a live Codex client smoke test.

## Next gate

If the CLI validator passes, run a user-approved client smoke test with a temporary profile and no persistent credentials. If it fails, preserve the exact CLI diagnostic and fix only the failing manifest contract.
