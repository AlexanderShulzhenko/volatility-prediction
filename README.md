# Short-term Volatility Prediction
![repo_preview_wide_new](https://github.com/AlexanderShulzhenko/volatility-prediction/assets/80621503/167a7bfc-1d19-4f5c-897b-56bbb65b774c)

## Intro
This repo is a PoC stated in my paper, that could be found at ??. Model for predicting short-term volatility fluctuations is trained and explained, as well as a data processing pipeline, which includes data collection, preprocessing and feature engineering. We use Kedro as a framework to wrap all the code into the maintainable and easily configured pipelines. Essentially, project could be expressed in four main pipelines:
- [**Data collection**](https://github.com/AlexanderShulzhenko/volatility-prediction/blob/main/src/volatility_prediction_model/pipelines/data_collection/): optimized pipeline utilizing async requests to collect data using Binance REST API; 
- **Data combination**: combine klines `kedro.PartitionedDataset` into one `pd.DataFrame` for further analysis;
- **Feature engineering**: generate comprehensive list of features utilizing different techiques of analysis, e.g., time-series analysis, technical indicators, trades in-depth exploration, etc.;
- **Data science**: build, train and calibrate the model as well as create inference table for predictions assesment.

***Note***: for more detailed documentation refer to README files in the pipelines folder of current repo.

## Kedro usage
To run the model from end-to-end follow these steps:
1. Install kedro:
```
pip install kedro
```
2. Run data collection pipeline
```
kedro run --pipeline data_collection
```
3. Run data combination pipeline
```
kedro run --pipeline data_combination
```
4. Run feature engineering pipeline
```
kedro run --pipeline feature_engineering
```
5. Run data science pipeline
```
kedro run --pipeline data_science
```