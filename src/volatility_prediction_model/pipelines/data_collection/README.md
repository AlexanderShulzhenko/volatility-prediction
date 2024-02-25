# Data collection

![data_collection](https://github.com/AlexanderShulzhenko/volatility-prediction/assets/80621503/3118d39d-c9fb-4c7d-b673-c00a6b21d3d0)

Data collection pipeline provides scripts to scrap Bainance REST API in order to get data for the model. To main data sources used in the current project are:
- Candlestick data (OHLC);
- Trades data.

## Candlestick data

## Trades data
Trades data is leveraged to build unit-trades features by analysing the patterns of trades behavior before each timestamp in the master list. Pulling trades data is non-trivial exercise since the amount of data that should be pulled is huge and API calls take quite a while. Best practice to accelerate the requests is to use the async programming. We leveraged `aiohttp` library to make async API calls. Due to API limits imposed by Binance we had to introduce a special data structure called `branch`, where the collection of all branches are built on a `spine`. We are pulling data in batches (see figure above) not to violate API limits.

### Branch
> Branch is a structure (class in Python) that is defined as:
> ```python
> class branch:
>    def __init__(
>        self, flag: bool, trades_dct_list: list, start_stamp: str, end_stamp: str
>    ):
>        self.flag = flag
>        self.trades_dct_list = trades_dct_list
>        self.start_stamp = start_stamp
>        self.end_stamp = end_stamp
> ```

Branch is used to track all the batches pulled by an algorithm.

> Batch is the list of lists of *n* trades (where `n=1000` in our case), where each list of *n* trades correspond to a particular timestamp (see figure above).

When the batch is pulled it is distributed accordingly to the branches. When the branch is finished, i.e., when the latest trade timestamp is greater than specified in the branch definition, `flag` variable is assigned with `True`. This data structure helps to keep track of all trades lists with quering only those which are still not finished. 

> Spine is the basement for all branches, which is declared as list of empty branches. 
