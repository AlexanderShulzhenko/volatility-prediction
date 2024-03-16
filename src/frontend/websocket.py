import asyncio
import datetime as dt
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import websockets

klines_cols = [
    "start_time",
    "close_time",
    "symbol",
    "interval",
    "ft_id",
    "lt_id",
    "open",
    "close",
    "high",
    "low",
    "bav",
    "num_trades",
    "close_flag",
    "qav",
    "taker1",
    "taker2",
    "ignore",
]


st.set_page_config(
    page_title="Real-Time Data Science Dashboard",
    layout="wide",
)

st.title("Volatility Model Monitoring Dashboard")
st.sidebar.title("Model info")

# creating a single-element container
placeholder = st.empty()
line1 = st.sidebar.empty()
line2 = st.sidebar.empty()


def get_metrics(live_data):
    metrics = {}
    last_price = live_data["close"].iloc[-1]
    last_volume = live_data["bav"].iloc[-1]
    last_numt = live_data["num_trades"].iloc[-1]
    if len(live_data) > 1:
        prev_price = live_data["close"].iloc[-2]
        prev_volume = live_data["bav"].iloc[-2]
        prev_numt = live_data["num_trades"].iloc[-2]
    else:
        prev_price = last_price
        prev_volume = last_volume
        prev_numt = last_numt
    price_diff = last_price - prev_price
    volume_diff = last_volume - prev_volume
    numt_diff = last_numt - prev_numt

    metrics["last_price"] = last_price
    metrics["price_diff"] = price_diff
    metrics["last_volume"] = last_volume
    metrics["volume_diff"] = volume_diff
    metrics["last_numt"] = last_numt
    metrics["numt_diff"] = numt_diff

    return metrics


def streamlit_plot(live_data):
    with placeholder.container():
        # create two columns for charts
        fig_col1, fig_col2 = st.columns(2)
        with fig_col1:
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


async def f_timer():
    while True:
        mm = 15 - dt.datetime.now().minute % 15 - 1
        ss = 60 - dt.datetime.now().second - 1
        line1.markdown("Time to predictions update:")
        line2.markdown(f"## {mm:02d}:{ss:02d}")
        await asyncio.sleep(1)


async def listen_to_stream():
    data = []
    async with websockets.connect("wss://stream.binance.com:9443/ws/btcusdt@kline_1m") as websocket:
        while True:
            message = await websocket.recv()
            message = json.loads(message)
            data.append(message["k"])

            klines = pd.DataFrame().from_records(data)
            klines.columns = klines_cols
            klines["start_time"] = [dt.datetime.fromtimestamp(x / 1000.0) for x in klines["start_time"]]
            klines["close"] = klines["close"].astype(float)
            klines["bav"] = klines["bav"].astype(float)
            klines["num_trades"] = klines["num_trades"].astype(float)
            klines = klines.drop_duplicates(subset=["start_time"], keep="last")

            streamlit_plot(klines)


async def run_widgets():
    await asyncio.gather(listen_to_stream(), f_timer())


asyncio.run(run_widgets())
