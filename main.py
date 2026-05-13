import requests
import json
import boto3
from datetime import datetime


def fetch_top_coins():
    """Fetch top 10 coins from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1,
    }
    response = requests.get(url, params=params)
    return response.json()


def compute_kpis(coins):
    """Compute KPIs from raw coin data."""
    # Sort coins by 24h price change
    sorted_coins = sorted(coins, key=lambda c: c["price_change_percentage_24h"])

    top_gainers = sorted_coins[:3]
    top_losers = sorted_coins[-3:]

    # Compute average market cap across the top 10
    total_market_cap = sum(c["market_cap"] for c in coins)
    avg_market_cap = total_market_cap / len(coins)

    return {
        "timestamp": datetime.now().isoformat(),
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


def save_kpis(kpis):
    """Save KPIs to MinIO."""
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )
    s3.put_object(
        Bucket="crypto-kpis",
        Key="latest.json",
        Body=json.dumps(kpis, indent=2),
        ContentType="application/json",
    )


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
