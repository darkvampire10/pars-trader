# Security

Do not post credentials, raw Telegram updates, account statements or database backups in public issues.
For a vulnerability, contact the repository owner privately; do not disclose an exploit with live secrets.

Version 0.1 accepts only a configured Telegram owner in a private chat and has no public listening port.
It never accepts MT5 passwords through chat, stores no MT5 credentials, and contains no order executor.
Telegram itself receives messages typed to the bot: refusing persistence cannot erase that fact.

Keep `.env` mode 0600, protect `data/` and backups, use SSH authentication and rotate leaked tokens.
Do not run third-party scripts with account access without review. Do not expose a remote MT5 bridge publicly.
TLS validation is enabled by the standard-library client. Exception bodies/URLs are not logged.

The optional MT5 exporter reads its credentials from its private process environment; credentials are not
encrypted by that script and must be protected by the host. A production encrypted credential vault and
secure onboarding form are roadmap items, not current features.
