![Снимок экрана 2024-04-18 в 12 58 54](https://github.com/AlexanderShulzhenko/volatility-prediction/assets/80621503/892a6c5c-fd76-4c27-8628-a159174c2de9)
# Volatility model interface

Volatility model interface is powered by Streamlit, which allows to create interactive web-applications. Backend interface relies on the Kedro inference pipeline, which calls it using `runner.py` functionality.

Backend of the interface is designed to send updates of the widgets in a real-time. Backend uses Binance websocket (namely, `wss://stream.binance.com:9443/ws/btcusdt@kline_15m`) to get live data. Once the latest data is obtained, `run_kedro_pipeline()` is called to run inference pipeline.

To start the web-application use the following command in the terminal:
```
streamlit run src/frontend/websocket.py
```
## Interface snapshot
<img width="1432" alt="Снимок экрана 2024-04-18 в 13 04 26" src="https://github.com/AlexanderShulzhenko/volatility-prediction/assets/80621503/dcdff045-35c5-4571-93a9-1d94db7ec5c7">
