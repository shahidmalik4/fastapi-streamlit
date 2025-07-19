from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx
import asyncio
import time

app = FastAPI()
COINGECKO_API = "https://api.coingecko.com/api/v3"

# REST endpoints
@app.get("/price/{coin_id}")
def get_price(coin_id: str):
    url = f"{COINGECKO_API}/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_change": "true"
    }
    response = httpx.get(url, params=params)
    return response.json()

@app.get("/history/{coin_id}")
def get_history(coin_id: str, days: int = 1):
    url = f"{COINGECKO_API}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days
    }
    response = httpx.get(url, params=params)
    return response.json()

@app.get("/top-coins/")
def get_top_coins(limit: int = 20):
    url = f"{COINGECKO_API}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1
    }
    response = httpx.get(url, params=params)
    return [{"id": coin["id"], "name": coin["name"]} for coin in response.json()]

# ---------- WebSocket + Global Caching ----------

clients = set()
cached_prices = None
last_updated = 0
CACHE_DURATION = 60  # seconds

async def fetch_top_coins_price(limit=20):
    global cached_prices, last_updated
    now = time.time()

    if cached_prices is None or now - last_updated > CACHE_DURATION:
        print("Fetching new data from CoinGecko...")
        url = f"{COINGECKO_API}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "price_change_percentage": "24h"
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                cached_prices = [{
                    "id": coin["id"],
                    "symbol": coin["symbol"],
                    "name": coin["name"],
                    "current_price": coin["current_price"],
                    "market_cap": coin["market_cap"],
                    "price_change_percentage_24h": coin.get("price_change_percentage_24h"),
                } for coin in data]
                last_updated = now
        except httpx.HTTPStatusError as e:
            print(f"Error fetching data from CoinGecko: {e}")
    return cached_prices or []

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            prices = await fetch_top_coins_price()
            await websocket.send_json(prices)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        clients.remove(websocket)
