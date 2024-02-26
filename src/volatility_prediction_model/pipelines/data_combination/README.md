# Data Combination

This is a simple pipeline that combines `kedro.PartitionedDataset` of candlestick data into one `Parquet` file. The inputs (or the parts) of the `kedro.PartitionedDataset` are monthly-level data frames, which were loaded during the data collection step.

The combined file could be found in the `catalog.yaml`:

```yaml
concatenated_candlestick_data:
  type: pandas.ParquetDataset
  filepath: data/02_intermediate/concatenated_candlestick_data.pq
```

To open this file you can use `kedro` extesion for `Jupyter` by simply running:

```python
%load_ext kedro.ipython
df = catalog.load("concatenated_candlestick_data")
```
in the notebook opened from the project location.

The output of the combination pipeline is validated using `pandera.check_output()` function with the following schema:
```python
DataFrameSchema(
    {
        "open_time": Column(np.dtype("datetime64[ns]"), required=False),
        "open": Column(float, required=True),
        "high": Column(float, required=True),
        "low": Column(float, required=True),
        "close": Column(float, required=True),
        "volume": Column(float, required=True),
        "close_time": Column(np.dtype("datetime64[ns]"), required=True),
        "qav": Column(float, required=False),
        "num_trades": Column(int, required=True),
        "taker_base_vol": Column(float, required=False),
        "taker_quote_vol": Column(float, required=False),
    }
)
```
