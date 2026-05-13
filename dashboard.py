import streamlit as st
import boto3
import json

st.set_page_config(page_title="Crypto KPI Dashboard", page_icon="📊")
st.title("Crypto KPI Dashboard")

s3 = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
)

try:
    obj = s3.get_object(Bucket="crypto-kpis", Key="latest.json")
    data = json.loads(obj["Body"].read())
except Exception as e:
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
