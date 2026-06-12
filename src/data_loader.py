import yfinance as yf
import os
def load_data(ticker):
    print("Downloading Data...")
    data = yf.download(ticker,start="2020-01-01")
    return data