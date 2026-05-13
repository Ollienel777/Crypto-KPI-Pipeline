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


## Bug 2: NoSuchBucket crash + startup race condition
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


## Improvement — Environment variable config

MinIO endpoint, credentials, and bucket name were hardcoded identically in
`main.py`, `dashboard.py`, and `docker-compose.yml`. Rotating credentials
required touching three files.

Moved to `os.environ.get()` with defaults so the stack still works out of the
box. `docker-compose.yml` now passes them explicitly — switching environments
is a config change, not a code change.


## Improvement — Top volume KPI

Added a top-3-by-volume ranking to `compute_kpis()`. Volume is already in the
CoinGecko response so no extra API call needed.

Price change tells you what moved — volume tells you whether it had conviction
behind it. For liquidity providers specifically, the volume ranking surfaces
where the flow is concentrated regardless of direction. Renders as its own
section on the dashboard.

## What I'd do next:

With another two hours I'd add unit tests for compute_kpis() first. Both 
correctness bugs lived there and a test with known inputs would have caught 
them at commit time. 
After that, scheduling: the pipeline runs once and exits, which means the 
dashboard goes stale immediately. A simple cron job or loop with a 
configurable interval would make it actually useful. I'd also add structured 
logging to replace the print statements. When a pipeline run fails in 
production you need to know which step failed and why, and plain prints don't 
give you that. Finally, a MinIO healthcheck in docker-compose.yml so the 
startup race condition is fixed at the infrastructure level rather than just 
handled in application code.