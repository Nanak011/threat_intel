"""
STEP 2 - Stratified sample of 100 rows for manual audit

Pulls, from the CLEANED dataset:
    30 Low, 30 Medium, 20 High, 20 Critical
using a fixed random seed (reproducible - cite the seed in your methods section).

Sampling is done at the UNIQUE PAYLOAD level (not raw row level), so you're
not accidentally auditing the same repeated payload multiple times within
your 100.

Outputs an Excel workbook `audit_workbook.xlsx` with two sheets:
    - "label_me"    : id, ip, node, classification, summary, technique
                       (NO severity column - label this blind)
    - "answer_key"  : same ids with Gemini's cleaned severity + risk_score

Run:
    pip install --break-system-packages pandas openpyxl
    python 2_sample_for_audit.py
"""

import json
import random
import re
import pandas as pd

INPUT_PATH = "threat_feed_cleaned.json"
OUTPUT_XLSX = "audit_workbook.xlsx"

SEED = 42
SAMPLE_PLAN = {"Low": 30, "Medium": 30, "High": 20, "Critical": 20}

# Excel/openpyxl rejects most control characters (raw attacker payloads
# often contain them). Strip anything outside printable ASCII + common
# whitespace so the workbook actually writes.
ILLEGAL_XLSX_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)


def sanitize(value):
    if value is None:
        return ""
    text = str(value)
    return ILLEGAL_XLSX_CHARS.sub("", text)


def main():
    random.seed(SEED)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for i, row in enumerate(data):
        row["_row_id"] = i  # stable id for this run

    # Dedupe to one representative row per unique payload string, so the
    # audit sample isn't dominated by a few repeated payloads.
    seen_payloads = {}
    for row in data:
        key = row.get("technique") or f"__no_payload__{row['_row_id']}"
        if key not in seen_payloads:
            seen_payloads[key] = row
    unique_rows = list(seen_payloads.values())
    print(f"Deduplicated {len(data)} rows -> {len(unique_rows)} unique payloads.")

    by_severity = {}
    for sev in SAMPLE_PLAN:
        candidates = [r for r in unique_rows if r["severity"] == sev]
        by_severity[sev] = candidates
        print(f"  {sev}: {len(candidates)} unique payloads available")

    sampled_rows = []
    for sev, n in SAMPLE_PLAN.items():
        pool = by_severity[sev]
        if len(pool) < n:
            print(f"WARNING: only {len(pool)} unique '{sev}' payloads available, "
                  f"requested {n}. Taking all available.")
            n = len(pool)
        sampled_rows.extend(random.sample(pool, n))

    random.shuffle(sampled_rows)  # so severity isn't guessable from row order

    label_me = pd.DataFrame([{
        "audit_id": i + 1,
        "row_id": r["_row_id"],
        "ip": sanitize(r.get("ip")),
        "node": sanitize(r.get("node")),
        "classification": sanitize(r.get("classification")),
        "summary": sanitize(r.get("summary")),
        "technique": sanitize(r.get("technique")),
        "human_severity": ""  # <-- fill this in: Low / Medium / High / Critical
    } for i, r in enumerate(sampled_rows)])

    answer_key = pd.DataFrame([{
        "audit_id": i + 1,
        "row_id": r["_row_id"],
        "gemini_severity": r.get("severity"),
        "gemini_risk_score": r.get("risk_score"),
    } for i, r in enumerate(sampled_rows)])

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        label_me.to_excel(writer, sheet_name="label_me", index=False)
        answer_key.to_excel(writer, sheet_name="answer_key", index=False)

    print(f"\nSaved {OUTPUT_XLSX}")
    print("-> Fill in 'human_severity' on the 'label_me' sheet FIRST.")
    print("-> Only open 'answer_key' after you're done labeling all 100 rows.")
    print(f"Seed used: {SEED} (record this in your methods section)")


if __name__ == "__main__":
    main()