# Data Combination

This is a simple pipeline that combines `kedro.PartitionedDataset` of candlestick data into one `Parquet` file. The inputs (or the parts) of the `kedro.PartitionedDataset` are monthly-level data frames, which were loaded during the data collection step.

The combined file could be found in the `catalog.yaml`:

```yaml
concatenated_candlestick_data:
  type: pandas.ParquetDataset
  filepath: data/02_intermediate/concatenated_candlestick_data.pq
```
