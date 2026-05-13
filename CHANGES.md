Bug Fixes

## Bug 1: Gainers/losers ranking was inverted, None values handled incorrectly
`sorted()` is ascending by default, so `[:3]` is the three worst performers and
`[-3:]` is the three best. The variable names were inverted

Fix: swapped the slices and reversed the gainers list so the best performer appears
first. Also filtered out coins where `price_change_percentage_24h` is `None` before
sorting rather than coercing to `0.0`. On a bad market day a zero ranks above
genuinely negative values, which would surface a data-less coin as a top gainer.
Fixed `datetime.now()` → `datetime.now(timezone.utc)` — naive timestamps are
non-deterministic across container timezones.



