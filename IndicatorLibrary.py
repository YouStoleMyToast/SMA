#!/usr/bin/env python3
import time
import os,sys
import glob
from datetime import datetime,timedelta,timezone

import numpy as np
import pandas as pd
import pandas_ta as ta

from api_handler import FinancialModelingPrep as FMP


API = FMP()

def recurse(f,l):
    results = []
    for x in l:
        d = (f(x))
        if isinstance(d,pd.core.frame.DataFrame) and (d.shape[1] == results[0].shape[1]) if len(results) else True:
            results.append(d)
    return results

class TechnicalIndicatorLibrary():
    def __init__(self):
        self.stocklist = pd.read_csv("./data/stocklist.csv")
        self.blacklist = pd.read_csv("./data/technicalIndicatorSource/blacklist.csv")
        if not "technicalIndicatorSource" in os.listdir("./data/"):
            os.mkdir("./data/technicalIndicatorSource")
    
    def reshape_stocklist(self,max_size=5): #returns np.array of arrays with the inner arrays being as close to size as possible
        vals = self.stocklist["symbol"].values
        query_number = 2
        for i in range(1,max_size+1):
            if len(vals) % i == 0:
                query_number = i
        res = vals.reshape((query_number,int(len(vals)/query_number))).T
        return res

    def save_volatility(self,data):
        if len(data.symbol.unique()) > 1:
            raise Exception("Classifier->\n\tsave_volatility->\n\t\tThere Is More Than 1 Company Represented By The Data Trying To Be Saved.")
        symbol = str(data.iloc[0]["symbol"]).upper()
        thyme = datetime.now().strftime("%Y-%m-%d")
        filename = "_".join([symbol,thyme]) + ".xlsx"
        data.to_excel("./data/technicalIndicatorSource/" + filename,index=0)
        return 

    def add_to_blacklist(self,company):
        self.blacklist = self.blacklist.append({"symbol":company},ignore_index=True)
        self.blacklist.to_csv("./data/technicalIndicatorSource/blacklist.csv",index=0)
        return None

    def find(self,company,toDate):
        prefix = "./data/technicalIndicatorSource/"
        existing = glob.glob( prefix + str(company).upper() + "_*")
        if len(existing):
            filename = existing[0].replace(prefix,"")
            date = datetime.strptime(filename.split(".")[0].split("_")[1],"%Y-%m-%d")
            if date < toDate - timedelta(days=3):
                os.remove(existing[0])
                raise Exception("File Out Of Date.")
            return pd.read_excel(existing[0])
        else:
            raise Exception("No Existing Record Found")

    def retrieve(self,company):
        try:
            data = API.get_indicators(company=company).ta.reverse
            if data.shape[0]:
                self.save_volatility(data=data)
                return data
            raise Exception("technicalIndicatorsLibrary->Response was empty dataframe")
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            return self.add_to_blacklist(company)
    
    def get_data(self,company,strategy,toDate=datetime.now(),days=timedelta(days=200)):
        if isinstance(company,list):
            res = recurse(self.get_data,company,toDate,days)
            return pd.concat(res,ignore_index=True)
        if self.blacklist["symbol"].str.contains(company).sum() >= 1:
            print(f"{company} Has Been Blacklisted From Volatility Calculations")
            return None
        try:
            d = self.find(company=company,toDate=toDate)
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            d = self.retrieve(company=company)
        d.date = pd.to_datetime(d.date,format="%Y-%m-%d")
        d = d[d.date <= toDate ]
        d = d.iloc[ d.shape[0] - int(days.total_seconds() // (3600 * 24)) - 1 - 5 : -1]
        return (self.CalculateIndicators(d,strategy)).iloc[5:]

    def CalculateIndicators(self,data,indicatorSet=False):
        if indicatorSet == False:
            return data
        else:
            try:
                data.ta.strategy(indicatorSet)
            except KeyboardInterrupt:
                sys.exit(1)
            except Exception as e:
                raise Exception( "Invalid Indicator Set",e)
        return data

    def get(self,company,indicatorSet="all",toDate=datetime.now(),days=timedelta(days=200)):
        return self.get_data(company=company,strategy=indicatorSet,toDate=toDate,days=days)
        

    def run(self):
        queries = self.reshape_stocklist(max_size=1)
        for company in queries:
            try:
                data = self.get_data(company=list(company))
            except Exception as e:
                print("Exception",e)
                time.sleep(2)

    def update_all(self):
        self.stocklist = self.stocklist[~self.stocklist["symbol"].isin(self.blacklist["symbol"].to_list())]
        self.run()



def main():
    clc = TechnicalIndicatorLibrary()
    clc.update_all()
    return


if __name__ == "__main__":
    main()