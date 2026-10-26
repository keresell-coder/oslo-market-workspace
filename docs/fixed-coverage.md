# Fixed coverage — 2026-10-26

The 15 existing configured names are preserved. VSAT, COSH.OL, SCATC.OL, CMBTO.OL and ORK.OL are additive. The loader validates quote-market metadata independently of financial-statement currency. VSAT remains the exact NASDAQ symbol and USD quote currency; bare Oslo ticker normalization is unchanged.

Successful and failed fundamental refresh paths retain symbol/currency identity. Missing US quote currency is not replaced with NOK. NewsWeb returns unsupported for VSAT without making an Oslo issuer request. Technical rows absent from the independent Oslo producer remain explicit missing-source rows; no market-wide selection, ranking, rule or threshold is changed.

Verification: Python regression suite, static configuration/SQLite integration, US/Oslo success and stale-after-error tests, and separate real-source generation into an isolated candidate directory. JavaScript regression has one existing saved MOWI fixture failure, reproduced against the unchanged main baseline; only the session-scope header label changed in JavaScript; the saved benchmark and comparison renderer are unchanged. Retain source-health and comparison limitations. Publication is a separate reviewed action.
