# Data Directory

## Description

This directory is reserved for datasets used in the project.

The current implementation downloads historical market data dynamically using the `yfinance` library. Therefore, no raw datasets are stored in this repository.

## Data Source

- Provider: Yahoo Finance
- Accessed via: `yfinance`
- Primary Asset Used: SPY (S&P 500 ETF)

Example:

```python
from src.data_loader import load_data

df = load_data("SPY")
```

Future versions of this project may include locally stored datasets for reproducibility and survivorship-bias-free analysis.
