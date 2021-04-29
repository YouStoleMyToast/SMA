#!/usr/bin/env python3
import datetime
import numpy as np 
import pandas as pd 
import pandas_ta as ta 

from IndicatorLibrary import TechnicalIndicatorLibrary as TIL
from ProcessData import ProcessedDataLibrary as PDL
from classifier import ModelLibrary as ML 
from PricePrediction import PriceLibrary as PL 

def TestStrategy():
    return ta.Strategy(
        name="TEST",
        description="First Iteration Settings",
        ta=[
            {"kind":"macd"},
            {"kind":"slope","length":10},
            {"kind":"slope","length":3},
            {"kind":"midpoint"},
            {"kind":"fwma"},
            {"kind":"bbands"},
        ])

def useIndicatorLibrary(symbol,strategy,date,timespan):
    lib = TIL() 
    return lib.get(symbol,strategy,date,timespan)

def useProcessData(symbol,date,timespan):
    lib = PDL() 
    return lib.get(symbol,date,timespan)

def useClassifier(symbol,model,date,timespan):
    lib = ML()
    return lib.get(symbol,model,False,date,timespan)

def usePricePrediction(symbol,model,date,timespan):
    lib = PL(date)
    return lib.get(symbol,model,date,timespan)
















def showAll():
    symbol = "AAPL"
    upto = datetime.datetime(2021,3,15)
    timespan = datetime.timedelta(200)
    strategy = TestStrategy()

    print("indicators".upper())
    indicators = useIndicatorLibrary(symbol,strategy,upto,timespan)
    indicators.info()
    print(indicators)
    input("\n" * 3)

    print("processed".upper())
    processed = useProcessData(symbol,upto,timespan)
    processed.info()
    print(processed)
    input("\n" * 3)

    print("classification".upper())
    classification = useClassifier(symbol,"A",upto,timespan)
    classification.info()
    print(classification)
    input("\n" * 3)

    print("pricePrediction".upper())
    pricePrediction = usePricePrediction(symbol,"A",upto,timespan)
    pricePrediction.info()
    print(pricePrediction)


def main():
    # showAll()
    # exit()
    upto = datetime.datetime(2021,4,20)
    timespan = datetime.timedelta(200)
    data = usePricePrediction(["AAPL","PLUG","SQ","BA","TSLA"],"A",upto,timespan)
    print(data)

if __name__ == "__main__":
    main()
