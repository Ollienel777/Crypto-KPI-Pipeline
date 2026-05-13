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


## Bug 2 — NoSuchBucket crash + startup race condition
`save_kpis()` called `put_object` against a bucket that was never created.
Fixed with a `head_bucket` check first — creates only on 404, re-raises on
anything else so auth errors still surface.

Wrapped in a retry loop (5 attempts, 3s delay) because `depends_on: minio`
only waits for the container to start, not for MinIO to actually be ready.
On cold start the pipeline can fail before the hostname resolves or before
MinIO accepts connections — the retry covers both.


## Improvement on error handling

`fetch_top_coins()`: added `timeout=10` and `raise_for_status()` so network
hangs and non-200 responses fail loudly. Added a `ValueError` check if the
response isn't a non-empty list.

`dashboard.py`: the S3 call was at module level with no error handling —
any failure crashed the process before Streamlit could render anything. Wrapped
in a try/except with `st.error()` and `st.stop()` so the user sees a clean
message instead of a traceback.