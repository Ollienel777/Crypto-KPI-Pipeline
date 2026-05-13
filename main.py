import requests
import json
import time
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, EndpointResolutionError
from datetime import datetime, timezone


def fetch_top_coins():
    """Fetch top 10 coins from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Unexpected response from CoinGecko: {data}")
    return data


def compute_kpis(coins):
    """Compute KPIs from raw coin data."""
    # Sort coins by 24h price change
    ranked_coins = [c for c in coins if c["price_change_percentage_24h"] is not None]
    sorted_coins = sorted(ranked_coins, key=lambda c: c["price_change_percentage_24h"])

    top_gainers = sorted_coins[-3:][::-1]
    top_losers = sorted_coins[:3]

    # Compute average market cap across the top 10
    total_market_cap = sum(c["market_cap"] for c in coins)
    avg_market_cap = total_market_cap / len(coins)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "top_gainers": [
            {
                "name": c["name"],
                "symbol": c["symbol"],
                "change_24h": c["price_change_percentage_24h"],
            }
            for c in top_gainers
        ],
        "top_losers": [
            {
                "name": c["name"],
                "symbol": c["symbol"],
                "change_24h": c["price_change_percentage_24h"],
            }
            for c in top_losers
        ],
        "average_market_cap_usd": avg_market_cap,
        "total_market_cap_usd": total_market_cap,
    }


def save_kpis(kpis, retries=5, delay=3):
    """Save KPIs to MinIO."""
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )

    for attempt in range(1, retries + 1):
        try:
            try:
                s3.head_bucket(Bucket="crypto-kpis")
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    s3.create_bucket(Bucket="crypto-kpis")
                else:
                    raise

            s3.put_object(
                Bucket="crypto-kpis",
                Key="latest.json",
                Body=json.dumps(kpis, indent=2),
                ContentType="application/json",
            )
            return
        except (EndpointConnectionError, EndpointResolutionError):
            if attempt == retries:
                raise
            print(f"MinIO not reachable, retrying in {delay}s ({attempt}/{retries})...")
            time.sleep(delay)


def main():
    print("Fetching coins...")
    coins = fetch_top_coins()
    print(f"Fetched {len(coins)} coins")

    print("Computing KPIs...")
    kpis = compute_kpis(coins)

    print("Saving to MinIO...")
    save_kpis(kpis)

    print("Done!")


if __name__ == "__main__":
    main()
