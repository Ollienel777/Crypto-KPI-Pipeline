import os
import streamlit as st
import boto3
import json

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "crypto-kpis")

st.set_page_config(page_title="Crypto KPI Dashboard", page_icon="📊")
st.title("Crypto KPI Dashboard")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

try:
    obj = s3.get_object(Bucket=MINIO_BUCKET, Key="latest.json")
    data = json.loads(obj["Body"].read())
except Exception:
    st.error("No data available yet — run the pipeline first.")
    st.stop()

st.caption(f"Last updated: {data['timestamp']}")

col1, col2 = st.columns(2)
col1.metric("Total Market Cap", f"${data['total_market_cap_usd']:,.0f}")
col2.metric("Avg Market Cap (Top 10)", f"${data['average_market_cap_usd']:,.0f}")

st.subheader("📈 Top Gainers (24h)")
for coin in data["top_gainers"]:
    st.write(f"**{coin['name']}** ({coin['symbol'].upper()}): {coin['change_24h']:+.2f}%")

st.subheader("📉 Top Losers (24h)")
for coin in data["top_losers"]:
    st.write(f"**{coin['name']}** ({coin['symbol'].upper()}): {coin['change_24h']:+.2f}%")
