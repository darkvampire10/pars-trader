# Roadmap and acceptance criteria

## 0.1 — research foundation (this release)
Single-owner Persian Telegram command loop, persistent setup choices, snapshot strategy scanner,
freshness/news guards, pure risk sizing and paper exit engine, read-only optional MT5 exporter,
Docker definition, CI tests and install/update documentation.

## 0.2 — account connection
- HTTPS onboarding form, signed one-time sessions tied to Telegram owner; no secrets in query strings.
- Credential encryption at rest, separate managed key, rotation and deletion; never send credentials to AI.
- Actual terminal server resolution; demo/live detection and account identity binding.
- Equity reference persistence across partial exits/restarts; verified daily reset timezone and floors.
- News provider license/coverage; real event freshness monitoring.
- Broker profit calculator and tick/lot/stops/filling mode validation.

## 0.3 — demo execution
- Persistent order intent and broker reconciliation on timeout/restart.
- Netting/hedging differences, partial fills, rejected SL modifications and disconnections.
- Three target exits, break-even only after confirmed first exit; all state durable.
- Correlated USD exposure including manual positions and pending orders; no unknown unprotected exposure.
- Risk engine integration; account limits verified against actual panel rules.
- Chronological out-of-sample tests, spread, commissions, slippage, news and gap scenarios.
- Run on selected MT5 broker demo. No profit claims from synthetic tests.

## 1.0 — real execution, after the preceding acceptance tests
- Owner explicitly opts in, verified EA permission and account-specific rules.
- Kill switch, recovery drills, monitoring, backup/restore, audit logs and private security review.
- AI provider adapter with budget cap, sourced news and strict structured output.
- AI cannot override risk, invent prices or issue broker commands.

## Later
Multi-user tenant isolation, individual account runners, subscriptions, portfolio reports.
FeneFX cross-account copying restrictions must be checked before expanding to shared signals/execution.

## Test scope
Unit tests are synthetic and offline. They do not establish broker compatibility, connectivity,
Docker availability, execution quality, strategy returns or legal compliance.
