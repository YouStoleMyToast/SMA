#!/usr/bin/env python3
import os, sys
import glob

import numpy as np
import pandas as pd 
import datetime

from ProcessData import ProcessedDataLibrary as PDL




class PriceHandler:
    def __init__(self,toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        self.ProcessedData = PDL()
        self.toDate = toDate
        self.days = days
        return 

    def modelA( self, data ):
        data["currentPrice"] = data["currentPrice"].astype(np.float64)
        data["highPercentFromMid"] = data["highPercentFromMid"].astype(np.float64)
        data["lowPercentFromMid"] = data["lowPercentFromMid"].astype(np.float64)    
        
        current = data["currentPrice"].iloc[0]
        highFromMid = data["highPercentFromMid"].iloc[0]
        lowFromMid = data["lowPercentFromMid"].iloc[0]

        entry = current - (np.float(current) * (lowFromMid + .01))
        exit = current + (np.float(current) * (highFromMid + .01))
        percent_gain = (exit - entry) / exit
        return {
            "date":data["date"].iloc[0],
            "symbol":data["symbol"].iloc[0],
            "model":"A",
            "current": current,
            "entry":entry,
            "exit" : exit,
            "gainPotential":percent_gain,
        }

    def process(self, symbol , model="A",toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        if isinstance(symbol,list):
            return pd.concat([ self.process(s,model)  for s in symbol],ignore_index=1)
        data = self.ProcessedData.get(symbol,self.toDate,self.days)
        if model == "A":
            prediction = self.modelA(data)
            return pd.DataFrame([prediction])
        return False


class PriceLibrary():
    def __init__(self,toDate):
        self.handler = PriceHandler(toDate)
        basedir = "./data/Models/"
        if "Prices" not in os.listdir(basedir):
            os.mkdir(basedir + "Prices")
        self.basedir = basedir + "Prices/"
        return

    def find(self,symbol,model="A",toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        if symbol.upper() + ".csv" in os.listdir(self.basedir):
            data = pd.read_csv(self.basedir + symbol.upper() +  ".csv")
            data["date"] = pd.to_datetime(data["date"],format="%Y-%m-%d")
            data = data[(toDate - data["date"] + datetime.timedelta(3) <= datetime.timedelta(6)) & (data["model"] == model)]
            if data.shape[0]:
                return pd.DataFrame(data.iloc[-1]).T
        raise Exception("Data Not Found")

    def SaveData( self, data ):
        symbol = data["symbol"].iloc[0].upper()
        f = symbol + ".csv"
        if f in os.listdir(self.basedir):
            data = pd.concat( [ pd.read_csv( self.basedir + f ), data ],ignore_index=True)
        data.to_csv(self.basedir + f,index=0)
        return True

    def retrieve(self,symbol,model="A",toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        data = self.handler.process(symbol,model,toDate,days)
        if data.shape[0]:
            self.SaveData( data )
            return data
        raise Exception("No Data Available For This Symbol")

    def get(self,symbol,model="A",toDate=datetime.datetime.now(),days=datetime.timedelta(200)):
        if isinstance(symbol,list):
            res = []
            for s in symbol:
                try:
                    data = self.get(s,model,toDate,days)
                    res.append( data )
                except:
                    pass
            return pd.concat(res,ignore_index=True)
        try:
            data = self.find(symbol,model,toDate,days)
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            data = self.retrieve(symbol,model,toDate,days)
        data.current = data.current.astype(np.float64)
        data.entry = data.entry.astype(np.float64)
        data.exit = data.exit.astype(np.float64)
        data.gainPotential = data.gainPotential.astype(np.float64)
        return data
            


        








def load_symbols():
    d = "./data/Lists/"
    files = glob.glob(d + "BestOverall*.xlsx")
    f = files[0]
    best_list = pd.read_excel(f).iloc[:10]
    return list(best_list["symbol"])


def main():
    symbols = load_symbols()
    date = datetime.datetime(2021,3,15)
    process = PriceLibrary(toDate=date)


    # data = process.get(["PLUG","AAPL","GME","SPCE","APPS","TSLA","BA","GE"],toDate=date)
    # data.sort_values(by="gainPotential",axis=0,inplace=True)
    # data = data.round(3)
    # data.to_clipboard(excel=True,sep="\t",index=0)
    # print(data)
    # exit()


    symbols = pd.read_csv("./data/stocklist.csv")
    symbols = list(symbols["symbol"])
    res = []
    for i in range(50,len(symbols),50):
        try:
            data = process.get(symbols[i-50:i],toDate=date)
            data.sort_values(by="gainPotential",axis=0,inplace=True)
            # print(data)
            res.append( data )
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            pass

        # print(pd.concat(res,ignore_index=1))
    
    print(len(res))
    print(data)
    data = pd.concat(res,ignore_index=1)
    data.to_csv("./data/Lists/Prices/All.csv",index=0)



        

if __name__ == "__main__":
    main()
