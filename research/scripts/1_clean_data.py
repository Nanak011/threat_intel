"""
STEP 1 - Clean threat_feed.json

What this does:
  1. Loads the raw feed.
  2. Remaps out-of-schema severity values ("Informational", "Very Low", or
     anything else outside the 4-class set) into "Low".
  3. Groups all rows by their exact `technique` payload string.
  4. For every payload that appears more than once, resolves severity by
     MAJORITY VOTE across its occurrences. Ties are broken toward the
     HIGHER severity (conservative: fewer missed real threats).
  5. Writes:
       - threat_feed_cleaned.json   -> the cleaned dataset, same shape as input,
                                        every row's severity replaced with its
                                        payload group's resolved severity
       - cleaning_report.json       -> stats you can cite directly in your
                                        methods section (how many rows were
                                        remapped, how many payload groups were
                                        unstable, etc.)

Run:
    pip install --break-system-packages pandas   # if not already installed
    python 1_clean_data.py

Expects threat_feed.json in the same folder (or edit INPUT_PATH below).
"""

import json
from collections import Counter, defaultdict

INPUT_PATH = "threat_feed.json"
OUTPUT_PATH = "threat_feed_cleaned.json"
REPORT_PATH = "cleaning_report.json"

VALID_SEVERITIES = ["Low", "Medium", "High", "Critical"]
SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

# Any severity value not in VALID_SEVERITIES gets remapped to this.
# (Covers "Informational", "Very Low", typos, casing issues, etc.)
FALLBACK_SEVERITY = "Low"


def normalize_severity(raw_severity):
    """Step 2: force every value into the 4-class schema."""
    if raw_severity in VALID_SEVERITIES:
        return raw_severity
    return FALLBACK_SEVERITY


def resolve_majority(severities):
    """
    Given a list of severities for the same exact payload, return the
    majority-vote severity. Ties broken toward the higher severity.
    """
    counts = Counter(severities)
    max_count = max(counts.values())
    tied = [sev for sev, c in counts.items() if c == max_count]
    if len(tied) == 1:
        return tied[0]
    # tie -> pick the highest-ranked severity among tied options
    return max(tied, key=lambda s: SEVERITY_RANK[s])


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} raw rows.")

    # --- Step 2: normalize out-of-schema severities ---
    remapped_count = 0
    for row in data:
        original = row.get("severity")
        normalized = normalize_severity(original)
        if normalized != original:
            remapped_count += 1
        row["severity"] = normalized  # overwrite in place for now

    print(f"Remapped {remapped_count} rows with out-of-schema severity -> {FALLBACK_SEVERITY}.")

    # --- Step 3/4: group by exact payload, resolve majority vote ---
    by_payload = defaultdict(list)
    for row in data:
        payload_key = row.get("technique") or ""
        by_payload[payload_key].append(row)

    total_groups = len(by_payload)
    multi_occurrence_groups = 0
    unstable_groups = 0
    tie_broken_groups = 0
    rows_changed_by_majority_vote = 0

    for payload_key, rows in by_payload.items():
        severities = [r["severity"] for r in rows]
        if len(rows) > 1:
            multi_occurrence_groups += 1
            unique_sevs = set(severities)
            if len(unique_sevs) > 1:
                unstable_groups += 1

                counts = Counter(severities)
                max_count = max(counts.values())
                tied = [s for s, c in counts.items() if c == max_count]
                if len(tied) > 1:
                    tie_broken_groups += 1

                resolved = resolve_majority(severities)
                for r in rows:
                    if r["severity"] != resolved:
                        rows_changed_by_majority_vote += 1
                    r["severity"] = resolved

    print(f"Unique payload strings: {total_groups}")
    print(f"Payload groups with 2+ occurrences: {multi_occurrence_groups}")
    print(f"Of those, unstable (disagreeing labels): {unstable_groups} "
          f"({unstable_groups / multi_occurrence_groups * 100:.1f}%)")
    print(f"Groups where majority vote required a tie-break (-> higher severity): {tie_broken_groups}")
    print(f"Total rows whose severity changed due to majority-vote resolution: {rows_changed_by_majority_vote}")

    # --- Save cleaned dataset ---
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved cleaned dataset -> {OUTPUT_PATH}")

    # --- Save a report  ---
    final_dist = dict(Counter(r["severity"] for r in data))
    report = {
        "total_rows": len(data),
        "rows_remapped_out_of_schema": remapped_count,
        "fallback_severity_used": FALLBACK_SEVERITY,
        "unique_payload_strings": total_groups,
        "payload_groups_with_repeats": multi_occurrence_groups,
        "unstable_payload_groups": unstable_groups,
        "instability_rate_pct": round(unstable_groups / multi_occurrence_groups * 100, 2)
            if multi_occurrence_groups else 0,
        "groups_requiring_tie_break": tie_broken_groups,
        "rows_changed_by_majority_vote": rows_changed_by_majority_vote,
        "final_severity_distribution": final_dist,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved cleaning report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()