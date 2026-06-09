# Backtesting Bias Analysis

> **I thought my strategy was printing money. Then I discovered six ways backtests lie.**

A systematic forensic analysis of six major backtesting biases in algorithmic trading. This project demonstrates how seemingly profitable strategies can produce misleading results when biases are ignored, and how performance changes when each bias is corrected.

Instead of showcasing an optimized strategy with inflated returns, this repository focuses on intellectual honesty and reproducible quantitative research.

---

## Motivation

Many trading strategies appear highly profitable in backtests:

* High Sharpe ratios
* Smooth equity curves
* Low drawdowns
* Extraordinary returns

However, these results often collapse under scrutiny.

Professional quantitative researchers ask a different question:

> **What assumptions make these results look better than reality?**

This project investigates six common sources of distortion in backtesting and demonstrates their impact through practical Python implementations.

---

## Project Goals

This repository aims to:

* Demonstrate six major backtesting biases.
* Quantify the effect of each bias.
* Build reproducible research workflows.
* Present honest strategy evaluation practices.
* Showcase production-quality Python code.
* Develop skills relevant to quantitative research roles.

---

## The Six Biases

### 1. Look-Ahead Bias

Using information that would not have been available at the time of trade execution.

Example:

* Generating signals using today's close.
* Executing trades at today's open.

Impact:

* Artificially inflated returns.
* Unrealistically high Sharpe ratios.

---

### 2. Survivorship Bias

Excluding companies that failed or were delisted from the historical universe.

Example:

* Backtesting on today's S&P 500 constituents.

Impact:

* Overestimation of strategy robustness.
* Underestimation of downside risk.

---

### 3. Overfitting

Optimizing parameters excessively on historical data.

Example:

* Selecting SMA windows that maximize in-sample Sharpe.

Impact:

* Poor out-of-sample performance.
* False confidence.

---

### 4. Data Snooping Bias

Testing many strategies and reporting only the best result.

Example:

* Trying hundreds of parameter combinations.

Impact:

* Spurious discoveries.
* False statistical significance.

---

### 5. Transaction Costs

Ignoring the costs associated with trading.

Examples:

* Brokerage fees
* Exchange fees
* Taxes

Impact:

* Significant performance degradation.
* High-turnover strategies become unprofitable.

---

### 6. Slippage

Assuming execution occurs at observed prices.

Examples:

* Bid-ask spreads
* Market impact
* Partial fills

Impact:

* Reduced realized returns.
* Increased implementation risk.

---

## Repository Structure

```text
backtesting-bias-analysis/
├── notebooks/
│   ├── 00_baseline_strategy.ipynb
│   ├── 01_look_ahead_bias.ipynb
│   ├── 02_survivorship_bias.ipynb
│   ├── 03_overfitting_bias.ipynb
│   ├── 04_data_snooping_bias.ipynb
│   ├── 05_transaction_costs.ipynb
│   ├── 06_slippage_modeling.ipynb
│   └── 07_clean_final_strategy.ipynb
│
├── src/
│   ├── data_loader.py
│   ├── strategy.py
│   ├── metrics.py
│   └── plotting.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── images/
│
├── docs/
│
├── requirements.txt
├── LICENSE
├── README.md
└── .gitignore
```

---

## Methodology

The project follows a sequential framework.

### Step 1

Build an intentionally flawed baseline strategy.

### Step 2

Identify one bias.

### Step 3

Correct the bias.

### Step 4

Measure the change in performance.

### Step 5

Repeat for all six biases.

### Step 6

Construct a final bias-aware strategy.

---

## Baseline Strategy

Strategy:

* SMA crossover
* Long-only
* SPY ETF

Data:

* Yahoo Finance
* Daily frequency

Period:

* 2010–2023

Initial assumptions intentionally include biases.

The baseline acts as the "too good to be true" version of the strategy.

---

## Performance Metrics

The following metrics are computed throughout the analysis:

* Total Return
* CAGR
* Annualized Volatility
* Sharpe Ratio
* Sortino Ratio
* Calmar Ratio
* Maximum Drawdown
* Win Rate

---

## Example Comparison Table

| Scenario              | Total Return | Sharpe | Max Drawdown |
| --------------------- | -----------: | -----: | -----------: |
| Baseline              |          TBD |    TBD |          TBD |
| Fix Look-Ahead        |          TBD |    TBD |          TBD |
| Fix Survivorship      |          TBD |    TBD |          TBD |
| Fix Overfitting       |          TBD |    TBD |          TBD |
| Add Transaction Costs |          TBD |    TBD |          TBD |
| Add Slippage          |          TBD |    TBD |          TBD |
| Final Clean Strategy  |          TBD |    TBD |          TBD |

Replace the placeholder values with actual results after completing the notebooks.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/backtesting-bias-analysis.git

cd backtesting-bias-analysis
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch Jupyter:

```bash
jupyter lab
```

---

## Requirements

Core libraries:

```text
numpy
pandas
matplotlib
scikit-learn
scipy
yfinance
jupyterlab
requests
tqdm
```

Python version:

```text
Python 3.10+
```

---

## How to Use

Recommended notebook order:

1. 00_baseline_strategy.ipynb
2. 01_look_ahead_bias.ipynb
3. 02_survivorship_bias.ipynb
4. 03_overfitting_bias.ipynb
5. 04_data_snooping_bias.ipynb
6. 05_transaction_costs.ipynb
7. 06_slippage_modeling.ipynb
8. 07_clean_final_strategy.ipynb

Following this order tells the complete story of how the strategy evolves.

---

## Key Findings

This section will be updated after the analysis.

Expected outcomes include:

* Performance deteriorates as unrealistic assumptions are removed.
* Small implementation details materially affect results.
* Robustness matters more than headline returns.
* Honest backtests provide more value than spectacular ones.

---

## Skills Demonstrated

### Quantitative Finance

* Strategy evaluation
* Backtesting methodology
* Market microstructure awareness
* Risk measurement

### Statistics

* Out-of-sample testing
* Multiple hypothesis testing
* Parameter sensitivity
* Robustness analysis

### Python

* Data analysis
* Modular architecture
* Visualization
* Research workflows

### Software Engineering

* Reproducibility
* Version control
* Code organization
* Documentation

---

## Future Improvements

Potential extensions include:

* Walk-forward optimization
* Monte Carlo simulation
* Deflated Sharpe Ratio
* Probabilistic Sharpe Ratio
* Fama-French factor attribution
* GARCH volatility modeling
* Regime detection using Hidden Markov Models
* Order book simulation

---

## References

* Pardo, R. (2011). *The Evaluation and Optimization of Trading Strategies*.
* Bailey, D., & López de Prado, M. (2014). *The Deflated Sharpe Ratio*.
* Harvey, C., Liu, Y., & Zhu, H. (2016). *...and the Cross-Section of Expected Returns*.
* Brown, S., Goetzmann, W., & Ibbotson, R. (1992). *Survivorship Bias in Performance Studies*.
* Almgren, R., & Chriss, N. (2001). *Optimal Execution of Portfolio Transactions*.

---

## Disclaimer

This repository is intended solely for educational and research purposes.

It does not constitute investment advice, financial advice, or a recommendation to buy or sell any financial instrument.

Past performance does not guarantee future results.

---

## Author

**Shaurya Saxena**

BE CSE (Hons.) AI & ML, Chandigarh University

Interested in:

* Quantitative Research
* Machine Learning
* Statistical Modeling
* Algorithmic Trading
* Financial Data Science

If you found this repository useful, consider starring it and sharing feedback.
