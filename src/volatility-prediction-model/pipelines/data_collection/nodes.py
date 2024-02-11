import datetime as dt
import warnings
from typing import Dict

import pandas as pd
from binance.client import Client
from tqdm import trange

warnings.simplefilter(action='ignore', category=FutureWarning)


api_key = 'jpMZyoxdAxEpMcF0QObw9zSyvDNgKJdzuZFIOwxdu8RcP3vJ8TnZD3z9wceBHZz6'
api_secret = 'XbQcSmgZUDYx6VGqibCQeWgiqP4bBDQdHqiKxSCfEpTrHxRPBsmJIl9h2M4ggDUz'
client = Client(api_key, api_secret)

num_days = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31
}


def get_candlestick_data() -> Dict[str, pd.DataFrame]:
    data_collection = {}
    for year in [2021, 2022, 2023]:
        print(f"Loading year {year}...")
        for month in trange(1,13):
            interval='15m'

            klines = client.futures_historical_klines("BTCUSDT",
                                                    interval,
                                                    f"{year}-{month}-01T00:00:00Z",
                                                    f"{year}-{month}-{num_days[month]}T23:59:00Z"
                                                    )
            data = pd.DataFrame(klines)

            # create colums name
            data.columns = ['open_time',
                            'open',
                            'high',
                            'low',
                            'close',
                            'volume',
                            'close_time',
                            'qav','num_trades',
                            'taker_base_vol',
                            'taker_quote_vol',
                            'ignore']
            data['close_time'] = [dt.datetime.fromtimestamp(x/1000.0) for x in data['close_time']]
            data['open_time'] = [dt.datetime.fromtimestamp(x/1000.0) for x in data['open_time']]
            data['close'] = data['close'].astype('float')
            data['open'] = data['open'].astype('float')
            data['high'] = data['high'].astype('float')
            data['low'] = data['low'].astype('float')
            data['volume'] = data['volume'].astype('float')
            data_collection[f"{year}_{month}"] = data
    return data_collection
