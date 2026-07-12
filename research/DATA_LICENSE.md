# Data License

The datasets in this repository (`threat_feed.json`, `threat_feed_cleaned.json`,
`cleaning_report.json`, and any derived audit/results files) are licensed
separately from the source code, under:

**Creative Commons Attribution 4.0 International (CC BY 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format
- **Adapt** - remix, transform, and build upon the material

for any purpose, even commercially, under the following terms:

- **Attribution** - You must give appropriate credit, provide a link to
  this repository (and to the dataset's Zenodo DOI), indicate
  if changes were made, and do so in any reasonable manner, but not in any
  way that suggests the licensor endorses you or your use.
- No additional restrictions - You may not apply legal terms or
  technological measures that legally restrict others from doing anything
  the license permits.

Full legal text: https://creativecommons.org/licenses/by/4.0/legalcode

## Suggested citation

> [Gurunanak Adhikari]. *Multi-Node Honeypot Threat Intelligence
> Dataset*. [2026]. Available at: github.com/nanak011/threat_intel

## Notes on the data

This dataset contains attacker-originated IP addresses and raw HTTP
request payloads captured by a honeypot network with no legitimate
production traffic. It does not contain personal data about victims or
uninvolved third parties. Attacker IP addresses are published as-is, which
is standard practice for public threat-intelligence datasets (see e.g.
AbuseIPDB, DShield); no attempt is made to deanonymize or attribute
specific individuals behind the observed IP addresses.