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
    populate_data,
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
pred_stats = fig_col1.empty()
model_stats = fig_col2.empty()

# sidebar countdown
line1 = st.sidebar.empty()
line2 = st.sidebar.empty()


# metrics and candlesticks
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
            x=live_data["open_time"],
            open=live_data["open"],
            high=live_data["high"],
            low=live_data["low"],
            close=live_data["close"],
        )

        fig = go.Figure(data=candlestick, layout={"xaxis": {"rangeslider": {"visible": False}}})

        st.write(fig)


# model upd metrics, feature values, model predictions barchart
async def plot_model(live_data):
    stats = await get_model_stats(live_data)
    with model_stats.container():
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(
            label="Last update",
            value=str((stats["time"] + dt.timedelta(minutes=15)).time().strftime("%H:%M:%S")),
        )
        kpi2.metric(
            label="True update time",
            value=dt.datetime.now().time().strftime("%H:%M:%S"),
        )
        kpi3.metric(
            label="Prediction",
            value=str(round(100 * stats["prediction"], 1)) + "%",
            delta=str(round(100 * (stats["prediction"] - stats["prev_prediction"]))) + "%",
        )

        st.markdown("### Detailed prediction values")

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(
            label="GKHV",
            value=round(stats["GKHV"] * 1e4, 1),
            delta=round(1e4 * (stats["GKHV"] - stats["prev_GKHV"]), 1),
        )
        kpi2.metric(
            label="BBW",
            value=round(stats["bbw"] * 1e2, 3),
            delta=round(1e2 * (stats["bbw"] - stats["prev_bbw"]), 3),
        )
        kpi3.metric(
            label="Line slope",
            value=round(stats["coef"], 1),
            delta=round(stats["coef"] - stats["prev_coef"], 1),
        )

        st.image("/Users/alexshulzhenko/PycharmProjects/model/data/08_reporting/inference_waterfall.png")

    with pred_stats.container():
        data = stats["data"][-30:].reset_index(drop=True)
        # Add one more row to match the new "growing" candlestick
        last_row = pd.DataFrame().from_dict(
            {
                "open_time": [stats["time"] + dt.timedelta(minutes=15)],
                "prediction": [0],
            }
        )
        data = pd.concat([data, last_row]).reset_index(drop=True)
        bar = go.Bar(
            x=data["open_time"],
            y=data["prediction"],
        )

        st.markdown("### Latest predicted values")

        fig = go.Figure(data=bar, layout={"xaxis": {"rangeslider": {"visible": False}}})
        st.write(fig)


async def f_timer():
    while True:
        mm = 15 - dt.datetime.now().minute % 15 - 1
        ss = 60 - dt.datetime.now().second - 1
        line1.markdown("Time to predictions update:")
        line2.markdown(f"## {mm:02d}:{ss:02d}")
        await asyncio.sleep(1)


# TODO: properly cut klines (no need to store full df)
async def listen_to_stream():
    data = []
    init_klines = populate_data(num_records=100, symbol="BTCUSDT", interval="15m")
    state = len(init_klines) - 1
    async with websockets.connect("wss://stream.binance.com:9443/ws/btcusdt@kline_15m") as websocket:
        while True:
            message = await websocket.recv()
            message = json.loads(message)
            data.append(message["k"])

            klines = pd.DataFrame().from_records(data)
            klines.columns = KLINES_COLS
            klines["open_time"] = [dt.datetime.fromtimestamp(x / 1000.0) for x in klines["open_time"]]
            klines["close_time"] = [dt.datetime.fromtimestamp(x / 1000.0) for x in klines["close_time"]]
            klines["close"] = klines["close"].astype(float)
            klines["bav"] = klines["bav"].astype(float)
            klines["num_trades"] = klines["num_trades"].astype(float)
            klines["close_flag"] = klines["close_flag"].astype(bool)

            klines = pd.concat([init_klines, klines]).reset_index(drop=True)
            klines = klines.drop_duplicates(subset=["open_time"], keep="last").reset_index(drop=True)

            await streamlit_plot(klines[-30:].reset_index(drop=True))

            if len(klines) > state:  # new candlestick had closed
                await plot_model(klines[:-1])
                state = len(klines)
            print(klines["close_time"].iloc[-1])


async def run_widgets():
    await asyncio.gather(listen_to_stream(), f_timer())


asyncio.run(run_widgets())
