import asyncio
import datetime as dt
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import websockets
from utils import (
    KLINES_COLS,
    get_metrics,
    get_model_stats,
)

# titles
st.set_page_config(
    page_title="Real-Time Data Science Dashboard",
    layout="wide",
)

st.title("Volatility Model Monitoring Dashboard")
st.sidebar.title("Model info")

# containers for stats and model
fig_col1, fig_col2 = st.columns(2)
live_stats = fig_col1.empty()
model_stats = fig_col2.empty()

# sidebar countdown
line1 = st.sidebar.empty()
line2 = st.sidebar.empty()


async def streamlit_plot(live_data):
    # create two columns for charts
    with live_stats.container():
        kpi1, kpi2, kpi3 = st.columns(3)

        metrics = get_metrics(live_data)
        kpi1.metric(
            label="Latest price",
            value=round(metrics["last_price"], 2),
            delta=round(metrics["price_diff"], 2),
        )
        kpi2.metric(
            label="Latest volume",
            value=round(metrics["last_volume"], 2),
            delta=round(metrics["volume_diff"], 2),
        )
        kpi3.metric(
            label="Num. Trades",
            value=round(metrics["last_numt"], 2),
            delta=round(metrics["numt_diff"], 2),
        )

        st.markdown("### Live price chart")

        candlestick = go.Candlestick(
            x=live_data["start_time"],
            open=live_data["open"],
            high=live_data["high"],
            low=live_data["low"],
            close=live_data["close"],
        )

        fig = go.Figure(data=candlestick, layout={"xaxis": {"rangeslider": {"visible": False}}})

        st.write(fig)


async def plot_model(live_data):
    stats = await get_model_stats(live_data)
    with model_stats.container():
        st.markdown(f"### Updated predictions with state {stats} at {dt.datetime.now()}")


async def f_timer():
    while True:
        mm = 15 - dt.datetime.now().minute % 15 - 1
        ss = 60 - dt.datetime.now().second - 1
        line1.markdown("Time to predictions update:")
        line2.markdown(f"## {mm:02d}:{ss:02d}")
        await asyncio.sleep(1)


async def listen_to_stream():
    data = []
    state = 0
    async with websockets.connect("wss://stream.binance.com:9443/ws/btcusdt@kline_1m") as websocket:
        while True:
            message = await websocket.recv()
            message = json.loads(message)
            data.append(message["k"])

            klines = pd.DataFrame().from_records(data)
            klines.columns = KLINES_COLS
            klines["start_time"] = [dt.datetime.fromtimestamp(x / 1000.0) for x in klines["start_time"]]
            klines["close"] = klines["close"].astype(float)
            klines["bav"] = klines["bav"].astype(float)
            klines["num_trades"] = klines["num_trades"].astype(float)
            klines["close_flag"] = klines["close_flag"].astype(bool)
            klines = klines.drop_duplicates(subset=["start_time"], keep="last")

            await streamlit_plot(klines)

            if len(klines) > state:  # new line was added
                await plot_model(klines)
                state = len(klines)


async def run_widgets():
    await asyncio.gather(listen_to_stream(), f_timer())


asyncio.run(run_widgets())
