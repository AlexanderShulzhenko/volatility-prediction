# Data collection

![data_collection](https://github.com/AlexanderShulzhenko/volatility-prediction/assets/80621503/3118d39d-c9fb-4c7d-b673-c00a6b21d3d0)

Data collection pipeline provides scripts to scrap Bainance REST API in order to get data for the model. To main data sources used in the current project are:
- Candlestick data (OHLC);
- Trades data.

## Candlestick data

## Trades data
Trades data is leveraged to build unit-trades features by analysing the patterns of trades behavior before each timestamp in the master list. Pulling trades data is non-trivial exercise since the amount of data that should be pulled is huge and API calls take quite a while. Best practice to accelerate the requests is to use the async programming. We leveraged `aiohttp` library to make async API calls. Due to API limits imposed by Binance we had to introduce a special data structure called `branch`, where the collection of all branches are built on a `spine`.

### Branch
> Branch is a structure (python class) that is defined as:
> ```lang-python
> class branch:
>    def __init__(
>        self, flag: bool, trades_dct_list: list, start_stamp: str, end_stamp: str
>    ):
>        self.flag = flag
>        self.trades_dct_list = trades_dct_list
>        self.start_stamp = start_stamp
>        self.end_stamp = end_stamp
> ```
