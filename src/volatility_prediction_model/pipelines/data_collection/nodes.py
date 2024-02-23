import datetime as dt
import warnings
from datetime import datetime, timedelta
from typing import Dict

import numpy as np
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


def _convert_to_date(x: pd.Series) -> pd.Series:
    return pd.to_datetime(x)


def _replace_value(x: pd.Series) -> pd.Series:
    return x.replace(-1, 1)


def clean_master_list(master_list: pd.DataFrame) -> pd.DataFrame:
    master_list["close_time"] = _convert_to_date(master_list["close_time"])
    master_list["target"] = _replace_value(master_list["target"])
    return master_list


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


def get_transactions_by_timestamps(t1: datetime,
                                   t2: datetime,
                                   symbol: str,
                                   verbose: bool=False) -> pd.DataFrame:
    '''
    Get all trades between two timestamps for the given symbol.

    Inputs:
    -------
        - t1 (datetime.datetime): start time.
        - t2 (datetime.datetime): end time.
        - symbol (str): symbol (pair).
        - verbose (bool): flag to print info.
    Outputs:
    -------
        - trades_df (pd.DataFrame): data frame with all trades between t1 and t2
    '''
    t1_stamp = t1.timestamp() * 1000
    t2_stamp = t2.timestamp() * 1000

    trades = client.get_aggregate_trades(startTime = int(t1_stamp),
                                         endTime = int(t2_stamp),
                                         symbol=symbol)
    df = pd.DataFrame.from_records(trades)
    try:
        df.columns = ['TradeID',
                      'Price',
                      'Quantity',
                      'FirstTradeID',
                      'LastTradeID',
                      'Time',
                      'Type',
                      'BestMatchFlg']
        df['Type'] = np.where(df['Type'], 'SELL', 'BUY')
        df['Time'] = df['Time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
        df['Price'] = df['Price'].astype(float)
        df['Quantity'] = df['Quantity'].astype(float)
        df['Amount'] = df['Price'] * df['Quantity']

        trades_df = df
        num_calls = 0
        while df['Time'].iloc[-1] < t2:
            last_trade_id = df['TradeID'].iloc[-1] + 1
            trades = client.get_aggregate_trades(fromId = str(last_trade_id),
                                             symbol=symbol,
                                             limit=1000)
            num_calls += 1

            df = pd.DataFrame.from_records(trades)
            df.columns = ['TradeID', 'Price', 'Quantity', 'FirstTradeID', 'LastTradeID', 'Time', 'Type', 'BestMatchFlg']
            df['Type'] = np.where(df['Type'], 'SELL', 'BUY')
            df['Time'] = df['Time'].apply(lambda x: datetime.fromtimestamp(x / 1000))
            df['Price'] = df['Price'].astype(float)
            df['Quantity'] = df['Quantity'].astype(float)
            df['Amount'] = df['Price'] * df['Quantity']

            trades_df = pd.concat((trades_df, df)).reset_index(drop=True)

        trades_df = trades_df[trades_df['Time'] < t2]

        if verbose:
            print('Number of API calls: \t', num_calls)
            print('Transactions from \t', trades_df['Time'].min(), 'to \t', trades_df['Time'].max())
            print('Total # of transaction:\t', len(trades_df))
    except ValueError:
        if verbose:
            print('Empty Data Frame:', str(t1), str(t2))
        trades_df = pd.DataFrame()

    return trades_df


def get_trades_data(master_list: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    trades_collection = {}
    for i in trange(len(master_list)):
        t2 = dt.datetime(master_list['close_time'][i].year,
                        master_list['close_time'][i].month,
                        master_list['close_time'][i].day,
                        master_list['close_time'][i].hour,
                        master_list['close_time'][i].minute,
                        0
                        ) + timedelta(minutes=1)
        t1 = t2 - timedelta(minutes=15)

        trades = get_transactions_by_timestamps(t1=t1, t2=t2, symbol='BTCUSDT')

        # check if empty
        if len(trades) > 0:
            trades_cleaned = trades.drop(columns=['TradeID',
                                                  'FirstTradeID',
                                                  'LastTradeID',
                                                  'BestMatchFlg',
                                                  'Amount',
                                                  'Time'])
            trades_cleaned['Price'] = trades_cleaned['Price'].astype('float32')
            trades_cleaned['Quantity'] = trades_cleaned['Quantity'].astype('float32')
        trades_collection[f"{i}"] = trades_cleaned
    return trades_collection
