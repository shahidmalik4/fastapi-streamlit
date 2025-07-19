# 💰 Real-Time Crypto Tracker

This is a full-stack **real-time cryptocurrency tracker** built with:

- 🧠 **FastAPI** – Backend REST API & WebSocket server  
- 🎨 **Streamlit** – Frontend UI  
- 📡 **WebSockets** – Real-time updates  
- 📊 **Plotly** – Interactive historical charts  
- 🔗 **CoinGecko API** – Live market data source  

---

## 🚀 Features

✅ Top cryptocurrencies (auto-updating)  
✅ Real-time price & market cap via WebSocket  
✅ Live 24h change with 🔴/🟢 indicators  
✅ Display of absolute price change  
✅ Currency selector (USD, EUR, INR, PKR, etc.)  
✅ Sort by price, market cap, change %  
✅ Interactive 30-day historical line chart  
✅ Optimized with API response caching  

---

## 🛠 Requirements

Install dependencies with:

```bash
pip install fastapi uvicorn httpx streamlit pandas plotly
```

Optional: create a `requirements.txt`:

```
fastapi
uvicorn
httpx
streamlit
pandas
plotly
```

---

## 📁 Project Structure

```
crypto-tracker/
│
├── main.py           # FastAPI backend with REST & WebSocket
├── streamlit.py      # Streamlit frontend UI
├── README.md         # Project documentation
└── requirements.txt  # (Optional) Dependencies
```

---

## ▶️ Running the Project

### Step 1: Run FastAPI Backend

```bash
uvicorn main:app --reload
```

Runs at: `http://localhost:8000`  
WebSocket: `ws://localhost:8000/ws/prices`

---

### Step 2: Run Streamlit Frontend

```bash
streamlit run streamlit.py
```

Runs at: `http://localhost:8501`

---

## 📡 FastAPI Endpoints

| Method | Endpoint                                | Description                            |
|--------|-----------------------------------------|----------------------------------------|
| GET    | `/price/{coin_id}`                      | Get current price, market cap, 24h %   |
| GET    | `/history/{coin_id}?days=30`            | 30-day historical chart data           |
| GET    | `/top-coins/?limit=20`                  | List of top N coins                    |
| WS     | `/ws/prices`                            | WebSocket for real-time top coin data  |

---

## ⚙️ How WebSocket Works

- Clients connect to `/ws/prices`  
- Server sends **live data** every 5 seconds  
- CoinGecko API is hit **only once per minute**  
- Multiple users reuse the **cached result**

✅ Efficient and avoids API rate limit errors

---

## ⚠️ Notes on CoinGecko API

- Free tier allows ~50–100 requests/min  
- This project uses **global cache** in the backend  
- Ensures performance and stability for many users  

---

## 🌟 Future Improvements

- Multi-day chart options (7D, 90D, 1Y)  
- Search/autocomplete for any coin  
- Portfolio tracker & wallet simulator  
- Backend deployment (Fly.io / Railway)  
- Streamlit hosting (Streamlit Cloud)  

---

## 👨‍💻 Author

Built using:

- [FastAPI](https://fastapi.tiangolo.com/)  
- [Streamlit](https://streamlit.io/)  
- [CoinGecko API](https://www.coingecko.com/en/api)  
- [Plotly](https://plotly.com/)  

---

## 📜 License

MIT License – free to use and modify!
