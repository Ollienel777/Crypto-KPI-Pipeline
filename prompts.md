# AI Prompt History

Model: Claude Sonnet 4.6 via Claude Code

---

**Prompt 1**
I'm going to read through this codebase and tell you what I find before writing any code. Don't suggest fixes yet unless prompted, I want to identify the issues first and use you to validate my thinking.

**Prompt 2**
Good, that matches most of what I found.
1. compute_kpis() sorts ascending but takes [:3] as top_gainers. The slices are backwards.
2. save_kpis() calls put_object on a bucket that's never created.
3. depends_on: minio in Compose only waits for the container to start, not for MinIO, creates a race condition on cold starts
4. No error handling anywhere, API, MinIO
5. All config is hardcoded, endpoint, credentials, bucket name.
Does anything look wrong with my analysis or is there something I missed?

**Prompt 3**
ready to implement, lets do one fix at a time, don't move onto the next fix until I confirm the current one looks good.
Fix 1: correct the gainers/losers logic in compute kpis. use datetime.now(timezone.utc).isoformat() for the timestamp
only touch compute_kpis() and the datetime import, nothing else yet

**Prompt 4**
before sorting, filter out any coins where price_change_percentage_24h is None, don't use or 0.00, just exclude them from the calculation (don't let it influence ranking)

**Prompt 5**
switch to working directly in your main project directory instead of a worktree

**Prompt 6**
I made the [::-1] change myself, I want it to display the highest return first

**Prompt 7**
Fix 2: save_kpis() need

1. bucket creation, check with head_bucket, create only if it doesn't exist 
2. retry loop incase the pipeline starts before docker has finished registering minio hostname

**Prompt 8**
the retry catches EndpointResolutionError but we should also catch EndpointConnectionError right

**Prompt 9**
looks good, fix 3:

1. fetch_top_coins(): add a 10sec time out and response.raise_for_status(). If the response isn't a list or is empty, raise a valueerror.
2. dashboard.py: wrap the get_object call in a try/except that shows st.error

**Prompt 10**
change the dashboard error message to just st.error("No data available yet — run the pipeline first.") and drop the {e}. Showing the raw exception in the UI can leak internal details like the MinIO endpoint.

**Prompt 11**
fix 4:
move all hardcoded config to env variables with sensible defaults. both main and dashboard hardcoded minio endpoint, creds, and bucket name the same way. Requires changes in three places including docker-compose-yml.
use os.environ.get() with defaults so it still works out of the box. Update docker-compose-yml to pass the vars through explicitly. Don't change any other logic.

**Prompt 12**
dashboard.py has an unused e. Change to except Exception.

**Prompt 13**
I want to add one improvement that's relevant to what this pipeline is actually for, this data is most useful to traders and liquidity providers and for them volume matters as much as price change. Is this a good idea

**Prompt 14**
Im thinking about separate volume ranking. I think a standalone top 3 by volume ranking is a better trend signal, people care about where the flow is regardless of price direction. 

**Prompt 15**
keep it focused: one new KPI, surfaces cleanly on the dashboard as its own section.

**Prompt 16**
noticed the same issue as before, total_volume can also be none, would the sort will crash on none < float if there's missing data

**Prompt 16**
refactor main.py into three classes: CoinGeckoClient handles fetching, KPICalculator handles compute_kpis(), MinIOStorage handles save_kpis() including the retry logic and bucket creation
config (env vars) moves into init where relevant. main() stays as the entry point, just instantiates and calls them. No logic changes, pure restructuring.