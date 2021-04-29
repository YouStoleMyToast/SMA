#!/usr/bin/env python3
import numpy as np
import pandas as pd 
import pandas_ta as ta

import glob
import os,sys
import datetime
import math

from IndicatorLibrary import TechnicalIndicatorLibrary as TIL

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

class BasicHandler():
    def __init__(self):
        return

    def getColumns(self,data,prefix):
        cols = []
        if isinstance(prefix,str):
            prefix = list(prefix)
        for p in prefix:
            for c in list(data.columns):
                if c.startswith(p):
                    cols.append(c)
        return cols

    def getTimeElapsed(self,data):
        data.date = pd.to_datetime(data.date,format="%Y-%m-%d")
        data["timeElapsed"] = (data["date"] - data['date'].shift()).fillna(pd.Timedelta(seconds=0))
        return data
        
    def getColumnDifference(self,data,column,percentage=False):
        if percentage:
            data[column + "_change_percent"] = ((data[column] - data[column].shift(-1)) / data[column]).fillna(0)
        else:
            data[column + "_change"] = (data[column] - data[column].shift(-1)).fillna(0)
        return data

    def getMagnitude(self,data,col,periods=1):
        data = data.dropna(axis=0)
        stepSize = (data.shape[0] - 1)  // periods
        magnitudes = []
        # y1 = data[col].iloc[0]
        for i in range(0,data.shape[0]-stepSize+1,stepSize):
            y1 = data[col].iloc[i]
            y2 = data[col].iloc[i+stepSize]
            magnitudes.append( math.sqrt( y1**2 + y2**2 ) / data.close.iloc[i+stepSize])
        return sum(magnitudes) / periods
    

    def getIntersections(self,data,col_a,col_b):
        data.date = pd.to_datetime(data.date,format="%Y-%m-%d")
        la = data[col_a].to_list()
        lb = data[col_b].to_list()

        intersectionData = []
        intersections = []
        directions = []
        for i in range(1, len( la ) ):
            directions.append( la[i] - la[i-1])
            if len(directions) > 5:
                directions.pop(0)

            intersectionData.append(1) if la[i] > lb[i] else intersectionData.append(-1)
            if len(intersectionData) > 1 :
                if intersectionData[len(intersectionData) - 1 ] != intersectionData[ len( intersectionData ) - 2 ] or la[i] == lb[i]:
                    intersections.append({
                        "date" : data.date.iloc[i],
                        "event": ( f"{col_a} {('rise above') if intersectionData[-1] == 1 else ('dips below')} {col_b}" ),
                        "elapsed" : intersections[-1]["date"] - data.date.iloc[i] if len(intersections) else datetime.timedelta(days=0),
                        col_a : la[i],
                        col_b : lb[i],
                        "trend_direction" : "uptrend" if sum(directions) > 0 else "downtrend",
                    })
        return pd.DataFrame(intersections)

class BBANDShandler(BasicHandler):
    def __init__(self):
        return

    def getBBData(self,technicalData):
        technicalData.date = pd.to_datetime(technicalData.date,format="%Y-%m-%d")
        bbandsColumns = self.getColumns(technicalData,prefix="BB")
        boundary_map = {    "BBL":"low",    "BBM":"close",  "BBU":"high"   }
        bbData = { "date" : technicalData.date.to_list() }
        for key in boundary_map:
            for column in bbandsColumns:
                if column.count(key):
                    bbData[boundary_map[key]] = technicalData[boundary_map[key]].to_list()
                    bbData[key] = technicalData[column].to_list()
        return pd.DataFrame(bbData)
    
    def getSqueeze(self,bbData):
        bbData = self.getTimeElapsed(bbData)
        bbData["bandSize"] = [row["BBU"] - row["BBL"] for index,row in bbData.iterrows()]
        bbData["closeToMidpoint"] = [ abs(row["BBM"] - row["close"]) for index,row in bbData.iterrows()]
        average_band_size = bbData["bandSize"].mean()
        squeeze_data = bbData[bbData["bandSize"] < average_band_size]
        squeezes = []
        squeeze = 0
        for index,row in squeeze_data.iterrows():
            if row["timeElapsed"] == datetime.timedelta(days=1):
                squeeze += 1
            else:
                if squeeze:
                    squeezes.append(squeeze)
                    squeeze = 0
        average_time_in_squeeze = datetime.timedelta( sum(squeezes) / len(squeezes) ) if len(squeezes) else 0
        return {
            "averageSqueezeTime": average_time_in_squeeze,
            "averageBandsize" : average_band_size,
            "averageCloseToMidpoint" : bbData.closeToMidpoint.mean(),
        }


    def getFrequencyData(self,bbData):
        boundary_map = {    "BBL":"low",    "BBM":"close",  "BBU":"high"   }
        frequency_data = {}
        for key in boundary_map:
            intersections = self.getIntersections(bbData,boundary_map[key],key)
            frequency_data[boundary_map[key] + "CrossFrequency"] = intersections.elapsed.mean() if intersections.shape[0] else datetime.timedelta(days=0)
            frequency_data[boundary_map[key] + "CrossCount"] = intersections.shape[0]
        return frequency_data

    def getDistanceData( self, bbData ):
        bbData["highDistFromMid"] = [ (row["high"] - row["BBM"]) for index,row in bbData.iterrows()]
        bbData["lowDistFromMid"] = [ (row["BBM"] - row["low"]) for index,row in bbData.iterrows()]
        bbData["highPercentFromMid"] = [ (row["highDistFromMid"] / row["BBM"] ) for index,row in bbData.iterrows()]
        bbData["lowPercentFromMid"] = [ (row["lowDistFromMid"] / row["BBM"] ) for index,row in bbData.iterrows()]
        return {
            "highDistFromMid" : bbData["highDistFromMid"].mean(),
            "lowDistFromMid" : bbData["lowDistFromMid"].mean(),
            "highPercentFromMid" : bbData["highPercentFromMid"].mean(),
            "lowPercentFromMid" : bbData["lowPercentFromMid"].mean(),
        }
        
    def process(self,data):
        bbData = self.getBBData(data)
        squeezeData = self.getSqueeze(bbData)
        frequencyData = self.getFrequencyData(bbData)
        distanceData = self.getDistanceData(bbData)
        bbData =  squeezeData | frequencyData | distanceData
        return bbData

class MACDhandler(BasicHandler):
    def __init__(self):
        return 

    def getIntersections(self, data, col_a, col_b):
        intersections = super().getIntersections(data, col_a, col_b)
        intersections["signal"] = [ ("buy" if "above" in row["event"] else "sell") for index,row in intersections.iterrows() ]
        intersections["close"] = data[data.date.isin(intersections.date)].close.to_list()
        intersections["high"] = data[data.date.isin(intersections.date)].high.to_list()
        intersections["low"] = data[data.date.isin(intersections.date)].low.to_list()
        return intersections

    def getSignalData(self,intersections,Signal="buy"):
        signalData = intersections
        if Signal in ["buy","sell"]:
            signalData = signalData[signalData.signal == Signal]
        signalData = self.getColumnDifference(signalData,"close")
        signalData = self.getColumnDifference(signalData,"close",percentage=True)
        signalData = self.getTimeElapsed(signalData)
        return {
            "meanPriceChange" : signalData.close_change.mean(),
            "meanPriceChangePercent" : signalData.close_change_percent.mean(),
            "frequency" : signalData.timeElapsed.mean(),
        }

    def getMacdData(self,technicalData):
        macdCols = self.getColumns(technicalData,["MACD_","MACDs_"])
        intersections = self.getIntersections(technicalData,*macdCols)  
        buyData = self.getSignalData(intersections,Signal="buy")
        sellData = self.getSignalData(intersections,Signal="sell")
        buySellData = self.getSignalData(intersections,Signal="buy/sell")

        altSellData = self.getTimeElapsed(intersections)
        altSellData = self.getColumnDifference(altSellData,"close")
        altSellData = self.getColumnDifference(altSellData,"close",True)
        altSellData = altSellData[altSellData["signal"] == "sell"]


        return {
            "averageMacdIntersectionsPrice": intersections.close.mean(),
            "averageHoldTime"   : altSellData.timeElapsed.mean(),
            "averageChangePercent"  : altSellData["close_change_percent"].mean() ,
            "averagePriceDifference"    : altSellData["close_change"].mean(),
            "buyFrequency"  : buyData["frequency"] ,
            "sellFrequency" : sellData["frequency"],
            "meanBuyChangePercent"  : buyData["meanPriceChangePercent"] ,
            "meanSellChangePercent" : sellData["meanPriceChangePercent"],
            "crossOverFrequency"    : buySellData["frequency"],
            "crossoverCount"    : intersections.shape[0],
            "prevSignal"    : intersections.signal.iloc[-1] ,
            "prevSignalDate"    : intersections.date.iloc[-1],
            "prevSignalPrice"   : intersections.close.iloc[-1],
        }        


    def process(self,technicalData):
        technicalData.date = pd.to_datetime(technicalData.date,format="%Y-%m-%d")
        macdData = self.getMacdData(technicalData)
        return macdData



class ProcessData(BasicHandler):
    def __init__(self):
        self.TechnicalLibrary = TIL()
        self.BBhandler = BBANDShandler()
        self.MACDHandler = MACDhandler()
        return

    def getMagnitudes(self,technicalData):
        FibCol = self.getColumns(technicalData,"FWMA_")[0]
        return {
            "fibMagnitude" : self.getMagnitude(technicalData,FibCol,5),
            "emaMagnitude" : self.getMagnitude(technicalData,"ema",5),
        }

    def getSlopes(self,data):
        data = data.dropna(axis=0)
        slopeDiffs = [ abs(row["SLOPE_3"] - row["SLOPE_10"]) for index,row in data.iterrows() ]
        slopeDiffAverage = sum(slopeDiffs) / len(slopeDiffs)
        averagePos10day = data[data["SLOPE_10"] > 0].shape[0] / data.shape[0]
        averageNeg10day = data[data["SLOPE_10"] < 0].shape[0] / data.shape[0]
        return {
            "AverageSlopeDifference_3_10" : slopeDiffAverage,
            "PositiveSlopeTime_10" : averagePos10day,
            "NegativeSlopeTime_10" : averageNeg10day,
        }

    def process(self,symbol,strategy=TestStrategy(),toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        technical_data = self.TechnicalLibrary.get(symbol,TestStrategy(),toDate=toDate,days=days)
        bbands = self.BBhandler.process(technical_data)
        macd = self.MACDHandler.process(technical_data)
        magnitudes = self.getMagnitudes(technical_data)
        slopes = self.getSlopes(technical_data)
        data = {
            "date" : technical_data.date.iloc[-1],
            "timespan" : technical_data.shape[0],
            "symbol" : symbol,
            "currentPrice": technical_data.close.iloc[-1],
        } | bbands | macd | magnitudes | slopes
        return pd.DataFrame([data])

    
class ProcessedDataLibrary():
    def __init__(self):
        if not "processedData" in os.listdir("./data/"):
            os.mkdir("./data/processedData")
        self.DataProcessor = ProcessData()
        return 

    def getClosestRecord(self,data,date,days):
        data = data[data.timespan == days.total_seconds() // (3600 * 24)]
        if not data.shape[0]:
            return False,False
        data.date = pd.to_datetime(data.date,format="%Y-%m-%d")
        date_diffs = [(date - data.date.iloc[i]) if (date - data.date.iloc[i]) >= datetime.timedelta(0) else datetime.timedelta(999)  for i in range(data.shape[0])]
        recentData = data.iloc[date_diffs.index(min(date_diffs))]
        return (recentData.date,pd.DataFrame(recentData).T)


    def find(self,symbol,toDate,days):
        directory = "./data/processedData/"
        matches = glob.glob( directory + str(symbol).upper() + ".xlsx")
        if not matches:
            raise Exception("No Matching Files Found")
        if len(matches) > 1:
            raise Exception("Too Many Matching Files -: ./data/processedData/")
        match =  matches[0]
        data = pd.read_excel(match)
        if toDate:
            age,data = self.getClosestRecord(data,toDate,days)
            if not age or  (toDate - age  >  datetime.timedelta(days=7) or toDate - age < datetime.timedelta(0)):
                raise Exception("Data Is Old" if age else "No Data In That Timespan")
        return data


    def retrieve(self,symbol,toDate,days):
        processed_data = self.DataProcessor.process(symbol,toDate=toDate,days=days)
        self.Save(symbol,processed_data)
        return processed_data

    def Save(self,symbol,processedData):
        matches = glob.glob( "./data/processedData/" + str(symbol).upper() + ".xlsx")
        if matches:
            data = pd.read_excel(matches[0])
            processedData = pd.concat([data,processedData],ignore_index=True)
            processedData.date = pd.to_datetime(processedData.date,format="%Y-%m-%d")
        processedData.to_excel("./data/processedData/" + str(symbol).upper() + ".xlsx",index=0)
        return

    def get(self,symbol:str,toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        try:
            data = self.find(symbol=symbol,toDate=toDate,days=days)
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            data = self.retrieve(symbol=symbol,toDate=toDate,days=days)
        return data
        

pd.options.mode.chained_assignment = None



def main():
    PDL = ProcessedDataLibrary()
    for i in range(1,13):
        toDate = datetime.datetime(2020,i,28)
        for symbol in ["PLUG","AAPL","APPS","SQ","GME"]:
            for date in [ toDate - datetime.timedelta(days=(i*180)) for i in range(4) ]: #Dates up to toDate every 6 months for the past 18 months inclusive
                for t in [120,200,365,400]:
                    timespan = datetime.timedelta(t)
                    data = PDL.get(symbol,date,timespan)
                    print(data)
    return


if __name__ == "__main__":
    main()