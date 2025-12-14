# Decision Intelligence Evaluation Report

_Last updated: 2025-02-07_

---

## Dataset Summary

| Metric | Value |
| ------ | ----- |
| Evaluation Window | 2025-02-01T00:00:00Z → 2025-02-07T23:59:59Z |
| Total Records | 350 |
| Validated Records | 350 |
| Unvalidated Records | 0 |
| Unique Prompt Hashes | 10 |

### Provider/Model Distribution

| Provider | Model | Count |
| -------- | ----- | ----- |
| google | gemini-2.0-flash | 70 |
| google | gemini-1.5-pro | 63 |
| openai | gpt-4o | 59 |
| openai | gpt-4o-mini | 56 |
| anthropic | claude-sonnet-4-20250514 | 52 |
| anthropic | claude-3-haiku | 50 |

---

## Calibration Results

| Metric | Value | Interpretation |
| ------ | ----- | -------------- |
| Expected Calibration Error (ECE) | **0.2327** | Moderate miscalibration; confidence does not perfectly track accuracy. |
| Overconfidence Rate | 0.0599 | 6% of incorrect decisions had confidence ≥ 0.5. |
| Underconfidence Rate | 0.1293 | 13% of correct decisions had confidence ≤ 0.5. |
| Total Evaluated | 317 | Records with known correctness and non-null confidence. |

### Confidence Bins

| Bin | Count | Avg Confidence | Empirical Accuracy |
| --- | ----- | -------------- | ------------------ |
| 0.40–0.50 | 41 | 0.4608 | 1.0000 |
| 0.50–0.60 | 60 | 0.5538 | 1.0000 |
| 0.60–0.70 | 51 | 0.6368 | 0.9020 |
| 0.70–0.80 | 44 | 0.7698 | 0.8864 |
| 0.80–0.90 | 78 | 0.8476 | 0.9231 |
| 0.90–1.00 | 43 | 0.9386 | 0.9302 |

Lower confidence bins (0.40–0.60) show perfect empirical accuracy, indicating underconfidence in those ranges.

---

## Provider Comparison

| Provider | Model | Total | Mean Confidence | Block Rate | False Allow Rate | False Block Rate | Accuracy |
| -------- | ----- | ----- | --------------- | ---------- | ---------------- | ---------------- | -------- |
| google | gemini-2.0-flash | 70 | 0.7171 | 44.29% | 1.43% | 0% | **98.57%** |
| openai | gpt-4o | 59 | 0.6938 | 45.76% | 3.39% | 0% | 96.61% |
| anthropic | claude-3-haiku | 50 | 0.7074 | 48.00% | 6.00% | 0% | 94.00% |
| openai | gpt-4o-mini | 56 | 0.6820 | 57.14% | 7.14% | 0% | 92.86% |
| anthropic | claude-sonnet-4-20250514 | 52 | 0.7497 | 42.31% | 7.69% | 0% | 92.31% |
| google | gemini-1.5-pro | 63 | 0.7107 | 41.27% | 7.94% | 0% | 92.06% |

**Top performer**: `google/gemini-2.0-flash` (lowest false-allow rate, highest accuracy).

Full CSV: [provider_report.csv](provider_report.csv)

---

## Gate Effectiveness

| Metric | Value | Notes |
| ------ | ----- | ----- |
| Total Blocks | 162 | 46.3% of all decisions. |
| Evaluated Blocks | 0 | No annotated block outcomes (blocked requests not executed). |
| Precision | N/A | Insufficient data (blocked decisions lack downstream outcome by design). |
| Recall | N/A | Cannot compute without ground-truth harmful set. |
| False Block Cost | 0 | No confirmed false blocks observed. |
| False Allow Cost | 19 | 19 allowed decisions resulted in downstream failure. |

**Interpretation**: Gate is conservative—blocks ~46% of traffic with zero false-block evidence. 19 false-allows indicate threshold tuning opportunity.

---

## Determinism Checks

| Check | Result | Action Required |
| ----- | ------ | --------------- |
| Mixed Verdict Hashes | 10/10 | ⚠️ All prompt hashes show both ALLOW and BLOCK across runs. |
| Confidence Drift | 10/10 | ⚠️ All hashes show confidence delta > 0.2 (max: 0.57). |
| Provider Divergence | 1/10 | One hash diverges across providers (expected for multi-provider setup). |

**Root cause**: Simulated traffic uses random confidence/risk per request; same transcript → different outcomes.  
**Mitigation**: In production, ensure identical prompts yield identical LLM responses (temperature=0, seed pinned).

### Top Regression Candidates

| Prompt Hash (truncated) | Count | Confidence Drift |
| ----------------------- | ----- | ---------------- |
| `fb757f8c...` | 28 | 0.5735 |
| `b6e63d5c...` | 29 | 0.5451 |
| `e63a87f3...` | 41 | 0.5434 |

---

## Frozen Thresholds

| Parameter | Value | Justification |
| --------- | ----- | ------------- |
| `ML_RISK_THRESHOLD` | **0.7** | Blocks high-risk traffic; 162 blocks observed. |
| `LLM_CONFIDENCE_THRESHOLD` | **0.6** | Balances false-allow (19) vs throughput. |
| `blocked_providers` | `[]` | No provider-level blocks required. |
| `blocked_models` | `[]` | No model-level blocks required. |

**Threshold rationale**: Current settings yield ~95% overall accuracy with 46% block rate. Lowering `LLM_CONFIDENCE_THRESHOLD` to 0.55 could reduce false-allows but increase block rate.

---

## Known Failure Modes

1. **Underconfidence in low-confidence bins**: Decisions in 0.40–0.60 range are 100% accurate but flagged as uncertain.
2. **False-allows (19 incidents)**: Allowed decisions that failed downstream; review for threshold tightening.
3. **Determinism variance**: Simulated data shows expected prompt-hash regressions; production must enforce reproducibility.

---

## Baseline Contract

This report establishes the **baseline evaluation snapshot** for the decision intelligence system.

- **Commit tag**: `baseline-2025-02-07`
- **Ledger path**: `./data/decision_ledger.db`
- **Evaluation window**: 2025-02-01 → 2025-02-07

### Change Policy

> Any threshold or gate logic change requires a **new evaluation report** comparing before/after metrics.

---

_Generated by evaluation suite on 2025-12-14._
