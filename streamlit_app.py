import streamlit as st
import requests
import pandas as pd
import json
import threading
import time
from websocket import create_connection
import plotly.graph_objects as go

API_BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"

st.set_page_config(page_title="Crypto Tracker", layout="wide")
st.title("💰 Real-Time Crypto Tracker")

# --- Supported currencies ---
@st.cache_data(ttl=86400)
def get_supported_currencies():
    url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
    try:
        res = requests.get(url)
        return res.json()
    except:
        return ["usd", "eur", "btc", "eth"]

supported_currencies = get_supported_currencies()

currency_full_names = {
    "usd": "United States Dollar",
    "eur": "Euro",
    "pkr": "Pakistan Rupee",
    "inr": "Indian Rupee",
    "jpy": "Japanese Yen",
    "gbp": "British Pound Sterling",
    "aud": "Australian Dollar",
    "cad": "Canadian Dollar",
    "chf": "Swiss Franc",
    "cny": "Chinese Yuan",
    "sek": "Swedish Krona",
    "nzd": "New Zealand Dollar",
    "rub": "Russian Ruble",
    "try": "Turkish Lira",
    "krw": "South Korean Won",
    "brl": "Brazilian Real",
    "zar": "South African Rand",
    "sgd": "Singapore Dollar",
}

options = []
for code in sorted(supported_currencies):
    name = currency_full_names.get(code, "")
    display = f"{code.upper()} - {name}" if name else code.upper()
    options.append(display)

default_index = options.index("USD - United States Dollar") if "USD - United States Dollar" in options else 0
selected_display = st.selectbox("Select currency:", options=options, index=default_index)

currency = selected_display.split(" ")[0].lower()
currency_upper = currency.upper()

# --- Get top coins ---
top_coins_url = f"{API_BASE}/top-coins/?limit=20"
try:
    top_coins = requests.get(top_coins_url).json()
except:
    st.error("Failed to fetch top coins from API.")
    st.stop()

coin_ids = [coin["id"] for coin in top_coins]
coin_names = {coin["id"]: coin["name"] for coin in top_coins}

# --- Initial fetch to populate data so table shows on first load ---
def fetch_initial_prices():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency,
        "ids": ",".join(coin_ids),
        "order": "market_cap_desc",
        "per_page": len(coin_ids),
        "page": 1,
        "price_change_percentage": "24h"
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        return {coin['id']: coin for coin in res.json()}
    return {}

if 'prices_data' not in st.session_state or not st.session_state['prices_data']:
    st.session_state['prices_data'] = fetch_initial_prices()

# --- WebSocket listener in background thread ---
def ws_listener():
    ws_url = f"{WS_BASE}/ws/prices"
    while True:
        try:
            ws = create_connection(ws_url)
            while True:
                msg = ws.recv()
                if msg:
                    try:
                        data = json.loads(msg)
                        # If data is still a JSON string, decode again
                        if isinstance(data, str):
                            data = json.loads(data)
                        # Must be list of dicts now
                        st.session_state['prices_data'] = {item['id']: item for item in data}
                        st.experimental_rerun()
                    except Exception as e:
                        print(f"WS JSON decode error: {e}")
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            time.sleep(5)

if 'ws_thread_started' not in st.session_state:
    t = threading.Thread(target=ws_listener, daemon=True)
    t.start()
    st.session_state['ws_thread_started'] = True

# --- Prepare table rows ---
currency_symbols = {
    "usd": "$", "eur": "€", "pkr": "₨", "inr": "₹", "jpy": "¥",
    "gbp": "£", "aud": "A$", "cad": "C$", "chf": "CHF", "cny": "¥",
    "sek": "kr", "nzd": "NZ$", "rub": "₽"
}
symbol = currency_symbols.get(currency, currency_upper + " ")

rows = []
prices_data = st.session_state.get('prices_data', {})
for coin_id in coin_ids:
    coin_data = prices_data.get(coin_id)
    if not coin_data:
        continue

    name = coin_names[coin_id]
    price = coin_data.get("current_price") or coin_data.get(currency)
    market_cap = coin_data.get("market_cap") or coin_data.get(f"{currency}_market_cap")
    change_pct = coin_data.get("price_change_percentage_24h") or coin_data.get(f"{currency}_24h_change")

    if price is None or market_cap is None or change_pct is None:
        continue

    abs_change = price * (change_pct / 100)
    sign_abs = "+" if abs_change >= 0 else "-"
    abs_change_str = f"{sign_abs}{symbol}{abs(abs_change):,.2f}"

    trend_emoji = "🟢" if change_pct > 0 else "🔴"
    trend_text = f"{trend_emoji} {change_pct:+.2f}% ({abs_change_str})"

    rows.append({
        "Coin": name,
        f"Current Price ({currency_upper})": price,
        f"Market Cap ({currency_upper}) (B)": market_cap / 1e9,
        "24h Change": trend_text,
        "_sort_price": price,
        "_sort_market_cap": market_cap,
        "_sort_change": change_pct
    })

if not rows:
    st.warning("No price data available yet.")
else:
    df = pd.DataFrame(rows)

    # Sorting options
    sort_option = st.selectbox("Sort by:", options=[
        ("Price (High → Low)", "_sort_price", True),
        ("Price (Low → High)", "_sort_price", False),
        ("Market Cap (High → Low)", "_sort_market_cap", True),
        ("Market Cap (Low → High)", "_sort_market_cap", False),
        ("24h Change (High → Low)", "_sort_change", True),
        ("24h Change (Low → High)", "_sort_change", False),
    ], format_func=lambda x: x[0])

    sort_col = sort_option[1]
    ascending = not sort_option[2]

    df_sorted = df.sort_values(by=sort_col, ascending=ascending)
    display_df = df_sorted.drop(columns=["_sort_price", "_sort_market_cap", "_sort_change"])

    st.dataframe(display_df, use_container_width=True)

# --- Horizontal buttons to select coin for chart ---
coin_name_list = [coin_names[cid] for cid in coin_ids]
selected_coin_name = st.radio(
    "Select a coin to view 30-day price history:",
    coin_name_list,
    horizontal=True
)
selected_coin_id = [cid for cid, name in coin_names.items() if name == selected_coin_name][0]

@st.cache_data(ttl=300)
def fetch_historical_prices(coin_id, currency):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": currency, "days": "30"}
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return None
    data = res.json()
    prices = data.get("prices", [])
    df_prices = pd.DataFrame(prices, columns=["timestamp", "price"])
    df_prices["date"] = pd.to_datetime(df_prices["timestamp"], unit="ms")
    return df_prices[["date", "price"]]

hist_df = fetch_historical_prices(selected_coin_id, currency)

if hist_df is not None and not hist_df.empty:
    st.subheader(f"30-Day Price History for {selected_coin_name} ({currency_upper})")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist_df["date"],
        y=hist_df["price"],
        mode="lines+markers",
        line=dict(color="royalblue", width=2),
        marker=dict(size=4),
        name=f"Price ({currency_upper})"
    ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=f"Price ({currency_upper})",
        hovermode="x unified",
        template="plotly_dark",
        margin=dict(l=40, r=40, t=40, b=40),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Historical data not available for this coin.")
