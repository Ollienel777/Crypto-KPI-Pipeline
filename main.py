import os
import logging
import requests
import json
import time
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, EndpointResolutionError
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class CoinGeckoClient:
    def __init__(self):
        self.url = "https://api.coingecko.com/api/v3/coins/markets"

    def fetch_top_coins(self):
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1,
        }
        response = requests.get(self.url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError(f"Unexpected response from CoinGecko: {data}")
        return data


class KPICalculator:
    def compute_kpis(self, coins):
        ranked_coins = [c for c in coins if c["price_change_percentage_24h"] is not None]
        sorted_coins = sorted(ranked_coins, key=lambda c: c["price_change_percentage_24h"])

        top_gainers = sorted_coins[-3:][::-1]
        top_losers = sorted_coins[:3]

        total_market_cap = sum(c["market_cap"] for c in coins)
        avg_market_cap = total_market_cap / len(coins)

        top_volume = sorted(
            [c for c in coins if c["total_volume"] is not None],
            key=lambda c: c["total_volume"],
            reverse=True,
        )[:3]

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


class MinIOStorage:
    def __init__(self, retries=5, delay=3):
        self.bucket = os.environ.get("MINIO_BUCKET", "crypto-kpis")
        self.retries = retries
        self.delay = delay
        self.s3 = boto3.client(
            "s3",
            endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
            aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
        )

    def _ensure_bucket_exists(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                self.s3.create_bucket(Bucket=self.bucket)
            else:
                raise

    def save_kpis(self, kpis):
        for attempt in range(1, self.retries + 1):
            try:
                self._ensure_bucket_exists()
                self.s3.put_object(
                    Bucket=self.bucket,
                    Key="latest.json",
                    Body=json.dumps(kpis, indent=2),
                    ContentType="application/json",
                )
                logging.info("KPIs saved successfully to %s/latest.json", self.bucket)
                return
            except (EndpointConnectionError, EndpointResolutionError):
                if attempt == self.retries:
                    logging.error("MinIO not reachable after %d attempts, giving up.", self.retries)
                    raise
                logging.warning("MinIO not reachable, retrying in %ds (%d/%d)...", self.delay, attempt, self.retries)
                time.sleep(self.delay)


def main():
    client = CoinGeckoClient()
    calculator = KPICalculator()
    storage = MinIOStorage()

    logging.info("Fetching coins...")
    coins = client.fetch_top_coins()
    logging.info("Fetched %d coins", len(coins))

    logging.info("Computing KPIs...")
    kpis = calculator.compute_kpis(coins)

    logging.info("Saving to MinIO...")
    storage.save_kpis(kpis)

    logging.info("Done!")


if __name__ == "__main__":
    main()
