# PI2 Signal-to-Matcher Report

## Summary

The deterministic matrix covers all 25 Consumer Contract matchers.

- Direct explicit matches: 0
- Safe normalization candidates: 0
- Insufficient signals: 2
- Source not collected: 15
- Contract field mismatch: 5
- Inference required: 3
- Applicability-only blockers: 0

The two typed contracts are blocked by absent connectivity inputs. Five precise log patterns are included among `SOURCE_NOT_COLLECTED`. The remaining legacy rules either depend on uncollected sources or lack the closed executable semantics required for safe evaluation. Three state-correlation rules would explicitly require prohibited inference from indirect symptoms.

No alternative PI2 vertical slice is recommended.
