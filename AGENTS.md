# Working on Pars Trader

- Read README.md and docs/ROADMAP.md before changes. Preserve truthful release status.
- Python 3.11+; core and Telegram service use only the standard library.
- Run `python -m unittest discover -s tests -v` and `python -m pars_trader demo`.
- Never place credentials, real account records, raw Telegram updates or customer data in Git.
- Never silently enable execution. Version 0.1 contains NO real-order executor.
- Never invent FeneFX rules, an MT5 server identifier, calendar freshness or AI confidence.
- Strategy changes require tests for no lookahead; risk changes require boundary tests.
- Keep Persian installation/update docs synchronized with actual features.
- Make narrow commits. Use a branch + pull request for future changes to an established repo.
- No production database/schema migrations without versioned backup/restore instructions.
