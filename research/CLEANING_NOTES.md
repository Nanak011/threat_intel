# Data Cleaning Notes — threat_feed_cleaned.json

This file documents the changes applied to the original `threat_feed.json`
(produced by the automated Gemini 2.5 / Vertex AI labeling pipeline) to
produce `threat_feed_cleaned.json`. Original raw file is unmodified and
kept in the repository for provenance; this cleaned version is the
reference dataset for all downstream analysis.

## What the original file is

`threat_feed.json` is the output of an hourly GitHub Actions pipeline that
pulls unclassified honeypot logs from a Supabase backend and submits them
to Gemini 2.5 for structured classification (attack `classification`,
`severity`, `risk_score`, and a one-sentence `summary`), then stitches the
result back with the original metadata (`ip`, `node`, `timestamp`,
`technique` [raw HTTP request], `total_attacks`). Data was captured from a
three-node honeypot network (DigitalOcean droplets in London, New York,
and Bangalore) listening on port 80 only.

As of this snapshot: 47,598 rows, 5,095 unique attacker IPs.

## Changes applied

### 1. Schema normalization
The intended severity taxonomy is four classes: `Low`, `Medium`, `High`,
`Critical`. The raw pipeline output was not schema-enforced (no `Literal`
constraint on the model's structured output), and 71 rows contained
out-of-schema values (`"Informational"`, `"Very Low"`). These were
remapped to `Low`.

### 2. Majority-vote resolution of repeated-payload label instability
Rows were grouped by their exact raw payload (`technique` field, the raw
HTTP request text). Of 17,218 unique payload strings, 3,249 occurred more
than once. Of those, **1,641 (50.5%) had been assigned two or more
different severities by Gemini across separate occurrences** — i.e., the
identical request, byte-for-byte, was scored differently at different
points in time.

For every such group, all occurrences were reassigned the **majority-vote
severity** across the group. Ties (no single majority) were broken toward
the **higher** severity, on the principle that a false downgrade is
generally more costly than a false upgrade in a security-labeling context.
This affected 769 groups and changed the severity of 6,839 individual rows.

### 3. Manual verification (audit, not applied to the full dataset)
A stratified, blind-labeled sample of 100 unique payloads (30 Low, 30
Medium, 20 High, 20 Critical; fixed seed = 42) was manually labeled against
a CVSS-informed rubric and compared to Gemini's (cleaned) labels:

- Overall accuracy: 75.0%
- Cohen's kappa: 0.662 ("substantial" agreement)
- Accuracy/kappa with High+Critical merged into one tier: 87.0% / 0.803
  ("almost perfect") — indicating residual disagreement is concentrated at
  one specific boundary, not spread randomly across the scale.

**Identified pattern:** credential/configuration-file disclosure attempts
(e.g. `.env`, `credentials.yaml`, `terraform.tfstate.backup`) were scored
inconsistently by Gemini — anywhere from Medium to Critical — for payloads
of comparable real-world risk. Human audit consistently rated this category
as High (data-exposure risk, no confirmed remote code execution). This is
documented as a known limitation of the raw labels; a standardization rule
is recommended before using `severity` as a training target for any
downstream classifier (see project README / final report for details).

## File summary

| File | Description |
|---|---|
| `threat_feed.json` | Original, unmodified pipeline output |
| `threat_feed_cleaned.json` | Schema-normalized + majority-vote resolved (this document) |
| `cleaning_report.json` | Machine-readable version of the stats above |

## Reproducibility
Cleaning script and exact parameters (seed, tie-break rule) are included
in this repository under `/pipeline`. Re-running `1_clean_data.py` against
`threat_feed.json` reproduces `threat_feed_cleaned.json` deterministically.