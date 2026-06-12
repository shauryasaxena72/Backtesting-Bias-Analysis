import numpy as np
def total_return(equity_curve):
    equity_curve=equity_curve.dropna()
    return (equity_curve.iloc[-1]/equity_curve.iloc[0])-1

def sharpe_ratio(returns):
    return np.sqrt(252) * returns.mean()/returns.std()

def max_drawdown(equity_curve):
    rolling_max=equity_curve.cummax()
    drawdown=(equity_curve - rolling_max)/rolling_max
    return drawdown.min()