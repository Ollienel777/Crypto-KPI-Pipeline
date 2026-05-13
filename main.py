import os
import requests
import json
import time
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, EndpointResolutionError
from datetime import datetime, timezone

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "crypto-kpis")


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

    top_volume = sorted(coins, key=lambda c: c["total_volume"], reverse=True)[:3]

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
        "top_volume": [
            {
                "name": c["name"],
                "symbol": c["symbol"],
                "volume_24h": c["total_volume"],
            }
            for c in top_volume
        ],
        "average_market_cap_usd": avg_market_cap,
        "total_market_cap_usd": total_market_cap,
    }


def save_kpis(kpis, retries=5, delay=3):
    """Save KPIs to MinIO."""
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )

    for attempt in range(1, retries + 1):
        try:
            try:
                s3.head_bucket(Bucket=MINIO_BUCKET)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    s3.create_bucket(Bucket=MINIO_BUCKET)
                else:
                    raise

            s3.put_object(
                Bucket=MINIO_BUCKET,
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
