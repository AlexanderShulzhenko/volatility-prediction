# Volatility model interface

Volatility model interface is powered by Streamlit, which allows to create interactive web-applications. Backend interface relies on the Kedro inference pipeline, which calls it using `runner.py` functionality.

Backend of the interface is designed to send updates of the widgets in a real-time. Backend uses Binance websocket (namely, "wss://stream.binance.com:9443/ws/btcusdt@kline_15m") to get live data.
