#!/usr/bin/env python3
import math
import datetime
import os, sys
import glob

import numpy as np 
import pandas as pd 
import pandas_ta as ta

from IndicatorLibrary import TechnicalIndicatorLibrary as TIL
from ProcessData import ProcessedDataLibrary as PDL


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

class Classifier():
    def __init__(self):
        self.DataProcessor = PDL()
        self.IndicatorLib = TIL()

    def extractKeywords(self,processedData,keywords :list):
        columns = processedData.columns.to_list()
        result = {}
        for c in columns:
            for k in keywords:
                if c.lower().count(k.lower()):
                    if k.lower().count("freq") or k.lower().count("hold"):
                        processedData[c] = pd.to_timedelta(processedData[c])
                    result[c] = processedData[c].iloc[-1]
        return pd.Series(result)

    def getColumns(self,data,prefix):
        cols = []
        if isinstance(prefix,str):
            prefix = list(prefix)
        for p in prefix:
            for c in list(data.columns):
                if c.startswith(p):
                    cols.append(c)
        return cols

                    
    def computeBBANDS(self,processed):
        bbData = self.extractKeywords(processed,["low","high","close","squeeze","band"])
        bbData.averageSqueezeTime = pd.to_timedelta(bbData.averageSqueezeTime)
        high_over_mid = bbData.highCrossFrequency / bbData.closeCrossFrequency # How Often the  the high or low price hits respective band over how often the closing price reverts to the mean
        low_over_mid = bbData.lowCrossFrequency / bbData.closeCrossFrequency # The closer to 0 the less volatile.
        squeeze_over_close = (bbData.averageSqueezeTime) / bbData.closeCrossFrequency
        return {
            "highOverMid" : high_over_mid,
            "lowOverMid" : low_over_mid,
            "squeezeOverClose":squeeze_over_close
        }

    def computeMACD(self,processed):
        macdData = self.extractKeywords(processed,["mean","freq","crossover","signal","hold","buy","sell"])
        buy_over_sell = (macdData.buyFrequency) / (macdData.sellFrequency) 
        hold_over_crossover = (macdData.averageHoldTime) / (macdData.crossOverFrequency)
        buy_sell_change_percent_ratio = macdData.meanBuyChangePercent / macdData.meanSellChangePercent
        return {
            "buySellChangePercentRatio" : buy_sell_change_percent_ratio,
            "buyOverSellFrequency" : buy_over_sell,
            "holdOverCrossoverFrequency" : hold_over_crossover,
        }


    def computeFIBEMA(self,raw,processed,periods=5):
        processedMag = self.extractKeywords(processed,["Magnitude","ema"])
        raw = raw.dropna(axis=0)
        fib_col = self.getColumns(raw,"FWMA")[0]
        stepSize = (raw.shape[0] - 1)  // periods
        fibchanges = []
        emachanges = []
        for i in range(0,raw.shape[0]-stepSize+1,stepSize):
            fy1 = raw[fib_col].iloc[i]
            ey1 = raw["ema"].iloc[i]
            fy2 = raw[fib_col].iloc[i+stepSize]
            ey2 = raw["ema"].iloc[i+stepSize]
            fibchanges.append( ( fy2 - fy1 ) / fy2)
            emachanges.append( ( ey2 - ey1 ) / ey2)
        emaChangePercent = sum(emachanges) / len(emachanges)
        fibChangePercent = sum(fibchanges) / len(fibchanges)
        # The Higher These Ratios The Less Volatile The Stock
        ema_over_fib_change_percent_ratio =  emaChangePercent / fibChangePercent
        ema_over_fib_magnitude = processedMag.emaMagnitude / processedMag.fibMagnitude 
        return {
            "emaOverFibChangePercentRatio": ema_over_fib_change_percent_ratio,
            "emaOverFibMagnitude": ema_over_fib_magnitude,
            "emaFibMagnitudeDiff": processedMag.fibMagnitude - processedMag.emaMagnitude,
            "emaAverageChangePercent" : emaChangePercent,
            "fibAverageChangePercent" : fibChangePercent,
            "periods" : periods,
        }


    def modelA(self,computedData,do_volatility=True):
        # print(computedData)
        score = ( (computedData["buyOverSellFrequency"] * computedData["emaOverFibChangePercentRatio"]) \
             * computedData["buySellChangePercentRatio"] * (computedData["emaFibMagnitudeDiff"])    \
                *   (1/(computedData["highOverMid"]/computedData["lowOverMid"]))) / (1/abs(computedData["squeezeOverClose"]))

        return  {
                    "volatility_actual_score" : score ,
                    "volatility_relative_score" : abs(score ) 
                } | {
                    "mean_actual_score" : 1 -score ,
                    "mean_relative_score" : 1 - abs( score )
                } | {
                    "overall_score" : 1 - abs((score) - abs(1 - abs(score))),
                    "overall_relative_score" : abs(1 - abs( abs(score) - (1 - abs(score)))),
                }

    def modelB(self,computedData,do_volatility=True):
        # print(computedData)
        score = ( (computedData["buyOverSellFrequency"] * computedData["emaOverFibChangePercentRatio"]) \
             * computedData["buySellChangePercentRatio"] * (computedData["emaFibMagnitudeDiff"])    \
                *   (1/(computedData["highOverMid"]/computedData["lowOverMid"]))) / (1/abs(computedData["squeezeOverClose"]))

        return  {
                    "volatility_actual_score" : score ,
                    "volatility_relative_score" : abs(score ) 
                } | {
                    "mean_actual_score" : 1 -score ,
                    "mean_relative_score" : 1 - abs( score )
                } | {
                    "overall_score" : 1 - abs((score) - abs(1 - abs(score))),
                    "overall_relative_score" : abs(1 - abs( abs(score) - (1 - abs(score)))),
                }


    def process(self,symbol,model="A",do_volatility=True,strategy=TestStrategy(),toDate=datetime.datetime.now(),days=datetime.timedelta(days=200)):
        raw = self.IndicatorLib.get(symbol,strategy,toDate,days)
        processed = self.DataProcessor.get(symbol,toDate,days)
        MACDcomputed = self.computeMACD(processed)
        BBcomputed = self.computeBBANDS(processed)
        MAGcomputed = self.computeFIBEMA(raw,processed)
        computed = pd.Series(MACDcomputed | MAGcomputed | BBcomputed | {"model":model,"symbol":symbol} )
        if model == "A":
            score = self.modelA(computed,do_volatility)
        return {
            "date":toDate,
            "datasize":days,
            "model" : model,
            "symbol": symbol,
        }  | score
        

class ModelLibrary():
    def __init__(self):
        self.models = ["A"]
        self.mClassifier = Classifier()
        if "Models" not in os.listdir("./data/"):
            os.mkdir("./data/Models")
        for model in self.models:
            if model not in os.listdir("./data/Models/"):
                os.mkdir("./data/Models/" + model)

    def find(self,symbol,model="A",do_volatility=True,toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        existing = glob.glob(f"./data/Models/{model}/{symbol}.csv")
        if len(existing):
            data = pd.read_csv(existing[0])
            data.datasize = pd.to_timedelta(data.datasize)
            data.date = pd.to_datetime(data.date,format="%Y-%m-%d")
            data = data[((toDate + datetime.timedelta(3) - data.date < datetime.timedelta(days=6))  & (data.datasize == days))]
            data = data.sort_values(by="date",axis=0)
            if data.shape[0]:
                return data.iloc[-1:]
        raise Exception("Model Data Not Found..Retrieving")
    
    def retrieve(self,symbol,model="A",do_volatility=True,toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        newdata = self.mClassifier.process(symbol,model=model,do_volatility=do_volatility,toDate=toDate,days=days)
        newdata = pd.DataFrame([newdata])
        existing = glob.glob(f"./data/Models/{model}/{symbol}*.csv")
        if len(existing):
            data = pd.read_csv(existing[0])
            data.datasize = pd.to_timedelta(data.datasize)
            data.date = pd.to_datetime(data.date,format="%Y-%m-%d")
            data = pd.concat([data,newdata],ignore_index=1)
            data.to_csv(f"./data/Models/{model}/{symbol}.csv",index=0)
        else:
            newdata.to_csv(f"./data/Models/{model}/{symbol}.csv",index=0)
        return newdata


    def get(self,symbol,model="A",do_volatility=True,toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        if model not in self.models:
            raise Exception("Model Not In Available Models\n" + "\n".join(self.models))
        try:
            data = self.find(symbol,model=model,do_volatility=do_volatility,toDate=toDate,days=days)
        except Exception as e:
            # print(e)
            data = self.retrieve(symbol,model=model,do_volatility=do_volatility,toDate=toDate,days=days)
        return data
    

    def ScoreStocklist(self):
        if "Lists" not in os.listdir("./data/"):
            os.mkdir("./data/Lists")
        stocklist = pd.read_csv('./data/stocklist.csv')["symbol"].to_list()
        date = datetime.datetime(2021,3,15)
        days = datetime.timedelta(200)
        bestMeanReversion = bestVolatility = bestOverall = pd.DataFrame()
        for symbol in stocklist:
            if len(symbol) > 5:
                continue
            try:
                data = self.get(symbol,toDate=date,days=days)
                if data["overall_relative_score"].iloc[0] > 1:
                    continue 
                if not bestMeanReversion.shape[0]:
                    bestMeanReversion = bestVolatility = bestOverall = data
                else:
                    bestMeanReversion   = pd.concat([bestMeanReversion,data],ignore_index=True)
                    bestVolatility  = pd.concat([bestVolatility,data],ignore_index=True)
                    bestOverall = pd.concat([bestOverall,data],ignore_index=True)
                if bestMeanReversion.shape[0] > 101:
                    bestMeanReversion.sort_values(by="mean_relative_score",axis=0,inplace=True)
                    bestVolatility.sort_values(by="volatility_relative_score",axis=0,inplace=True)
                    bestOverall.sort_values(by="overall_relative_score",axis=0,inplace=True)
                    bestMeanReversion = bestMeanReversion.iloc[1:]                    
                    bestVolatility = bestVolatility.iloc[1:]
                    bestOverall = bestOverall.iloc[1:]

                bestOverall.to_csv(f"./data/Lists/BestOverall_{date}_{days}.csv",index=0)
                bestMeanReversion.to_csv(f"./data/Lists/BestMeanReversion_{date}_{days}.csv",index=0)
                bestVolatility.to_csv(f"./data/Lists/BestVolatility_{date}_{days}.csv",index=0)

                print(bestOverall)

            except Exception as e:
                print("Exception occurs Scoring Stocklist",e)

    

def main():
    cl = ModelLibrary()
    cl.ScoreStocklist()
    exit()
    date = datetime.datetime(2021,1,21)
    results = []
    for symbol in ["PLUG","AAPL","GME","SPCE","APPS","TSLA","BA","GE"]:
        try:
            results.append( cl.get(symbol,toDate=date) )
        except:
            pass
    data = pd.concat(results,ignore_index=True)
    print(data)
    for col in data.columns.to_list():
        if "relative" not in col and "date" not in col and "model" not in col and "symbol" not in col and "days" not in col:
            data.drop(col,axis=1,inplace=True)
    data.to_clipboard(excel=True,sep="\t",index=0)
        

if __name__ == "__main__":
    main()