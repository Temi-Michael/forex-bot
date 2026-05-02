## 2024-03-24 - Lazy evaluation in Deriv Strategy
**Learning:** The LDP strategy previously evaluated `extract_last_digit` unconditionally on the entire tick window array (default 500 ticks), even when strict modes (`strict_over`, `strict_under`) only require the final 4 ticks. This caused massive redundant processing per cycle.
**Action:** When working with arrays of historical ticks/candles, strictly evaluate data only within the required lookback window of the specific strategy execution path, avoiding top-level full-array transformations.
