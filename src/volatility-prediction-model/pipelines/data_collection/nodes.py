import datetime as dt
import warnings
from typing import List

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


def get_candlestick_data():
    data_collection = []

    for month in trange(1,13):
        interval='15m'

        klines = client.futures_historical_klines("BTCUSDT",
                                                interval,
                                                f"2023-{month}-01T00:00:00Z",
                                                f"2023-{month}-{num_days[month]}T23:59:00Z"
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
        data['close']=data['close'].astype('float')
        data['open']=data['open'].astype('float')
        data['high']=data['high'].astype('float')
        data['low']=data['low'].astype('float')
        data['volume']=data['volume'].astype('float')
        data_collection.append(data)
    return data_collection


def save_candlestick_data(data_collection: List[pd.DataFrame]):
    num = 0
    for d in data_collection:
        num += 1
        d.to_csv(f'2023_{num}.csv')
