# Feature engineering
![features](https://github.com/AlexanderShulzhenko/volatility-prediction/assets/80621503/cdc784b6-2404-4176-ba0e-9e12e0db32f4)

## Intro
This pipeline generated features from the primary layer tables. Feature engineering pipeline leverages `numba` for just-in-time compilation of certain function to improve the pipeline performance.

## Candlestick features
This section contains basic features that could be derived using OHLC data. 

## Indicators features
This section implements certain techincal indicators that are widely used, e.g., smoothed RSI, Bollinger bands and Stochactic oscilator. Interesting part of this section is the slope calculation for the last `n` time points, which in performed by the:
```python
@jit(nopython=True) 
def line_fit(
  target_values: np.array,
  window_size: int
  ) -> Tuple[List[float], List[float]]:
  # calculation body
  return coefs, r2s
```
This function is calculating slopes and $R^2$ metrics for each fit. 


## Trades features

## Stochastic features
