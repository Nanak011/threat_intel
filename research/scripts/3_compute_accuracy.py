"""
STEP 3 - Compute Gemini vs. human agreement, after you've filled in
'human_severity' on the 'label_me' sheet of audit_workbook.xlsx.
 
Reports:
    - overall accuracy
    - per-class precision / recall / F1
    - full 4x4 confusion matrix
    - Cohen's kappa (agreement corrected for chance - report this number,
      reviewers care about it more than raw accuracy)
    - a breakdown specifically of the High/Critical boundary, since that's
      the boundary your LOAO test depends on
 
Run:
    pip install --break-system-packages pandas scikit-learn openpyxl
    python 3_compute_accuracy.py
"""
 
import pandas as pd
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, cohen_kappa_score
)
 
WORKBOOK = "audit_workbook.xlsx"
LABELS = ["Low", "Medium", "High", "Critical"]
SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
 
 
def analyze_directional_bias(y_true, y_pred):
    """
    Checks whether Gemini's disagreements with the human labels lean toward
    OVER-escalating (predicting a higher severity than the human did) or
    UNDER-escalating (predicting lower). A model that's simply noisy would
    split roughly evenly; a model with a real bias will lean hard one way -
    which is what you want to know for LOAO, since it tells you whether the
    withheld "Critical" class is likely contaminated with over-escalated
    lower-severity logs.
    """
    over = 0
    under = 0
    correct = 0
    per_true_class_over = {l: 0 for l in LABELS}
    per_true_class_under = {l: 0 for l in LABELS}
 
    for t, p in zip(y_true, y_pred):
        if t not in SEVERITY_RANK or p not in SEVERITY_RANK:
            continue
        t_rank, p_rank = SEVERITY_RANK[t], SEVERITY_RANK[p]
        if p_rank == t_rank:
            correct += 1
        elif p_rank > t_rank:
            over += 1
            per_true_class_over[t] += 1
        else:
            under += 1
            per_true_class_under[t] += 1
 
    total_wrong = over + under
    print("\n" + "=" * 60)
    print("DIRECTIONAL BIAS ANALYSIS")
    print("=" * 60)
    print(f"Correct: {correct} | Gemini over-escalated: {over} | "
          f"Gemini under-escalated: {under}")
 
    if total_wrong > 0:
        over_pct = over / total_wrong * 100
        under_pct = under / total_wrong * 100
        print(f"Of all disagreements: {over_pct:.1f}% were over-escalation "
              f"(Gemini rated it MORE severe than the human), "
              f"{under_pct:.1f}% were under-escalation.")
 
        if over_pct >= 65:
            print("\n-> STRONG OVER-ESCALATION BIAS: Gemini systematically rates "
                  "logs as more severe than a human would. This means the "
                  "'Critical' class in the raw data likely contains a meaningful "
                  "share of logs a human would call High or lower. For a LOAO "
                  "study, this dilutes the withheld 'Critical' test set with "
                  "mislabeled non-Critical material.")
        elif under_pct >= 65:
            print("\n-> STRONG UNDER-ESCALATION BIAS: Gemini systematically rates "
                  "logs as less severe than a human would. Real Critical-level "
                  "threats may be leaking into the Low/Medium/High training pool, "
                  "which would let the model 'cheat' by having seen near-Critical "
                  "examples during LOAO training.")
        else:
            print("\n-> No strong directional bias - disagreements are roughly "
                  "balanced between over- and under-escalation, suggesting "
                  "genuine noise rather than a systematic calibration skew.")
 
    print("\nOver-escalations by true class (human label -> Gemini rated higher):")
    for l in LABELS:
        if per_true_class_over[l] > 0:
            print(f"  true_{l}: {per_true_class_over[l]} over-escalated")
    print("Under-escalations by true class (human label -> Gemini rated lower):")
    for l in LABELS:
        if per_true_class_under[l] > 0:
            print(f"  true_{l}: {per_true_class_under[l]} under-escalated")
 
 
def main():
    label_me = pd.read_excel(WORKBOOK, sheet_name="label_me")
    answer_key = pd.read_excel(WORKBOOK, sheet_name="answer_key")
 
    merged = label_me.merge(answer_key, on="audit_id", how="inner")
 
    expected_total = len(label_me)
    if len(merged) != expected_total:
        print(f"WARNING: {expected_total} rows in label_me but only {len(merged)} "
              f"matched to answer_key after merge - check audit_id alignment.")
 
    # basic validation
    missing = merged["human_severity"].isna() | (merged["human_severity"].astype(str).str.strip() == "")
    if missing.any():
        print(f"WARNING: {missing.sum()} rows have no human_severity filled in yet. "
              f"Excluding them from this run.")
        merged = merged[~missing]
 
    bad_labels = ~merged["human_severity"].isin(LABELS)
    if bad_labels.any():
        print("WARNING: some human_severity values don't match the expected "
              f"labels {LABELS} exactly (check spelling/casing):")
        print(merged.loc[bad_labels, ["audit_id", "human_severity"]])
        merged = merged[~bad_labels]
 
    y_true = merged["human_severity"]       # human = ground truth for this check
    y_pred = merged["gemini_severity"]       # Gemini = system being evaluated
 
    print(f"\nRows compared: {len(merged)}")
    if len(merged) < 100:
        print(f"NOTE: expected 100 rows in the audit sample, only {len(merged)} "
              f"were usable. Check for blank/misspelled human_severity entries "
              f"above, or rows dropped during merge, before citing these numbers "
              f"as your final n=100 result.")
    print()
 
    acc = accuracy_score(y_true, y_pred)
    print(f"Overall accuracy (Gemini vs. human): {acc * 100:.1f}%")
 
    kappa = cohen_kappa_score(y_true, y_pred, labels=LABELS)
    print(f"Cohen's kappa: {kappa:.3f}")
    print("  (0 = chance agreement, 1 = perfect agreement; "
          ">0.6 generally considered 'substantial' agreement)\n")
 
    print("Per-class precision / recall / F1:")
    print(classification_report(y_true, y_pred, labels=LABELS, zero_division=0))
 
    print("Confusion matrix (rows = human label, columns = Gemini label):")
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)
    cm_df = pd.DataFrame(cm, index=[f"human_{l}" for l in LABELS],
                          columns=[f"gemini_{l}" for l in LABELS])
    print(cm_df)
 
    analyze_directional_bias(list(y_true), list(y_pred))
 
    # Specifically check the High/Critical boundary, since LOAO validity
    # depends on this boundary being real and not just teacher noise.
    boundary = merged[merged["human_severity"].isin(["High", "Critical"])]
    if len(boundary) > 0:
        b_acc = accuracy_score(boundary["human_severity"], boundary["gemini_severity"])
        print(f"\nHigh/Critical boundary subset (n={len(boundary)}): "
              f"Gemini agreement = {b_acc * 100:.1f}%")
        disagreements = boundary[boundary["human_severity"] != boundary["gemini_severity"]]
        if len(disagreements) > 0:
            print("\nDisagreements on the High/Critical boundary:")
            print(disagreements[["audit_id", "ip", "classification",
                                  "human_severity", "gemini_severity"]])
 
    cm_df.to_csv("confusion_matrix.csv")
    merged.to_csv("audit_merged_results.csv", index=False)
    print("\nSaved confusion_matrix.csv and audit_merged_results.csv")
 
 
if __name__ == "__main__":
    main()