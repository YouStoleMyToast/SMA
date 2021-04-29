#!/usr/bin/env python3
import numpy as np
import pandas as pd 
import os, sys
import pandas_ta as ta
import datetime
import matplotlib.pyplot as plt

def TestStrategy():
    return ta.Strategy(
        name="TEST",
        description="First Iteration Settings",
        ta=[
            {"kind":"macd"},
            # {"kind":"vwap"},
            {"kind":"slope","length":10},
            {"kind":"slope","length":3},
            {"kind":"midpoint"},
            {"kind":"fwma"},
            {"kind":"bbands"},
        ])

def Plot(data,fields,axes,kind="line"):
    columns = list(data.columns)
    cols = []
    for f in fields:
        if isinstance(f,dict):
            for key in f:
                Plot(data,fields=f[key],axes=axes.twiny(),kind=key)
            continue
        for c in columns:
            if ( c.startswith(f) ):
                cols.append(c)
    # if "MACDh" in fields:
    #     data.plot(kind="bar",x="date",y=cols,ax=axes,xticks=np.arange(0,90,5))
    else:
        data.plot(kind=kind,x="date",y=cols,ax=axes)


def Plots(data,plots,save=False,show=True):
    if len(plots) < 4:
        rows = 1
        cols = len(plots)
    elif len(plots) == 4:
        rows = 2
        cols = 2
    elif len(plots) < 7:
        rows = 2
        cols = 3
    elif len(plots) < 10:
        rows = 3
        cols = 3
    else:
        raise Exception("Number Of Plots Cannot Exceed 9")

    fig, axes = plt.subplots(nrows=rows,ncols=cols,**{"figsize":(11,8)})
    fig.suptitle(data.symbol.iloc[0])
    plt.subplots_adjust(left=0.1, 
                        bottom=0.1,  
                        right=0.9,  
                        top=0.9,  
                        wspace=0.4,  
                        hspace=0.4)  

    index = 0
    for i in range(rows):
        for e in range(cols):
            index = i * cols + e
            if index == len(plots):
                plt.show()
                return
            Plot(data,plots[index],axes=axes[index])
    if save:
        if "plots" not in os.listdir("./data/"):
            os.mkdir("./data/plots")
        plt.savefig(f"./data/plots/{data.symbol.iloc[0]}_{data.shape[0]}_{str(data.date.iloc[-1]).split()[0]}.png",dpi=480)
    if show:
        plt.show()

def plotStrategy(data,strategy,save=False,show=True):
    if strategy == "test":
    # TEST STRATEGY
        plots = [
            ["low","high","close"],
            ["close","BBL","BBH"],
            ["MACD_","MACDs_"],
            ["ema","FWMA"],
            [ "SLOPE"],
            ["high","BBU"],
        ]
    elif strategy == "bbands":
        plots = [
            ["BBU","BBL","close"],
            ["BBU","high"],
            ["BBL","low"],
        ]
    elif strategy == "macd":
        plots = [
            ["MACD_","MACDs_"],
            # ["MACD"],
            ["MACDh"],
        ]
    elif strategy == "ma":
        plots = [
            ["ema","SMA","close"],
            ["FWMA","close"],
            ["SLOPE"],
        ]
    
    elif strategy == "volatility":
    #VOLATILITY STRATEGY
        plots = [
            ["high","low","close"],
            ["THERMO"],
            ["KC"],
            ["ACCBM"],
            ["BB"],
            ["DC"],
            # ["MASS"]
        ]
    elif strategy == "momentum":
    #MOMENTUM STRATEGY
        plots = [
            ["high","low","close"],
            ["INERTIA","close"],
            ["PVO"],
            ["STOCH"],
            ["FISHER"],
            ["TRIX"]
        ]

    Plots(data=data,plots=plots,save=save,show=show)
    return

from IndicatorLibrary import TechnicalIndicatorLibrary as TIL 
def main():
    lib = TIL()
    toDate = datetime.datetime(2021,4,1)
    timespan = datetime.timedelta(200)
    for symbol in ["AAPL","PLUG"]:
        data = lib.get(symbol,TestStrategy(),toDate,timespan)
        plotStrategy(data,"test",save=False,show=True)
    # stocks = pd.read_csv("./data/BestOverallList.csv")
    # print(stocks)
    # for symbol in stocks.symbol.to_list():
    #     data = lib.get(stocks,TestStrategy())
    #     print(data)


if __name__ == "__main__":
    main()