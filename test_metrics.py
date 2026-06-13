import pandas as pd
import numpy as np
from src.metrics import total_return,sharpe_ratio,max_drawdown
equity=pd.Series([50000,50320,52000,42000])
returns=equity.pct_change().dropna()
print("Total Returns : ",total_return(equity))
print("Sharpe Ratio : ",sharpe_ratio(returns))
print("Max Drawdown : ",max_drawdown(equity))