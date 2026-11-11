# letak-worker-milk-agro

ProcMon Process Class (stdin, Proc-protocol 1.1) used as the `detect` step of dp-letaky for the chain `milk-agro`.
The chain has no scraper: flyers are announced by an operator in the Source config.

Input (`check` / `run`): `announced` = `[{pdfUrl, title?, validFrom?, validTo?}]`, `state` = `{seen: [key]}`.
Item key `announced|<normalized pdfUrl>` (scheme and host lower-cased, fragment dropped); meta `{type: "announced", title?, validFrom?, validTo?}`
(absent dates are omitted). Invalid entries (not an absolute http(s) URL, non-ISO date, validTo < validFrom) -> `config_error`.
The class `letak-worker-metro` is the same code.

Tests: `python -m pytest -q tests`.
