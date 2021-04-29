#!/usr/bin/env python3
import numpy as np
import pandas as pd
import requests
from config import FINANCIAL_MODELING_PREP_API_TOKENS as API_TOKENS
from config import markets
from config import API_VERBOSE as VERBOSE

import datetime
import fileinput
import sys
import json
from addict import Dict
from pandas.io.json import json_normalize


class FinancialModelingPrep():
    def __init__(self):
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.token = API_TOKENS[0]

    def get(self,route):
        try:
            suffix = ("&" if "?" in route else "?") + "apikey=" + self.token
            url = (f'{self.base_url}/{route}/{suffix}').replace("3//","3/").replace("/&","&")
            print(url) if VERBOSE else None
            res = requests.get(url=url)
            if "Error Message" in res.json():
                raise Exception(res["Error Message"])
            json_data = res.json()
            return pd.DataFrame(json_data) if "quote" in url else json_data
        except Exception as e:
            for i in range(len(API_TOKENS)):
                if API_TOKENS[i] == self.token and i < len(API_TOKENS) - 1:
                    self.token = API_TOKENS[ i + 1 ]
                    return self.get(route=route)
            raise Exception("API Keys likely Exhausted" + str(e))

    def get_stocklist(self):
        try:
            data = pd.read_csv('./data/stocklist.csv')
            return data
        except:
            self.make_stocklist()
            return self.get_stocklist()


    def make_stocklist(self): #retrieve a new stocklist and overwrite any existing 
        route = "/stock/list"
        data = self.get(route=route)
        data = pd.DataFrame(data)
        # data = data[len(data["symbol"]) < 5]
        data = data[data.exchange.isin(markets)]
        data = data[data.price > 0]
        data.drop("price",axis=1,inplace=True)
        data.to_csv("./data/stocklist.csv",index=0)
        return data

    def get_quote(self,company): #takes a string symbol or a list of string symbols (real time)
        if isinstance(company,list):
            company = ",".join(company)
        route = "/quote/" + company
        data = self.get(route=route)
        return data

    #params = {charttime=[1min,5min,15min,30min,1hour,4hour]}
    def get_historical(self,company,from_date=False,end_date=datetime.datetime.now(),price_only=False,timeDIFF=datetime.timedelta(weeks=12),full=False,charttime="4hours"):
        if from_date == False:
            from_date = datetime.datetime.now() - timeDIFF
        from_date = str(from_date).split()[0]
        end_date = str(end_date).split()[0]
        if isinstance(company,list):
            company = ",".join(company)
        route = "/historical-price-" + ("full" if full else "chart/" + charttime) + "/" + company + "?from=" + from_date+ "&to=" + end_date + ( 'seriestype=line' if price_only else "" )
        json_data = self.get(route=route)
        results = []
        for x in json_data:
            for index,row in pd.DataFrame(json_data[x]).iterrows():
                try:
                    s = pd.DataFrame(row['historical'])
                    s['symbol'] = [ row['symbol'] for _ in range(s.shape[0]) ]
                    results.append(s)
                except Exception as e:
                    print(f"API Handler: get_historical Exception -> {e}")
        result = pd.concat(results,ignore_index=True)
        return result

    def get_indicators(self,company,span="daily",period=100,kind="ema"):
        if isinstance(company,list):
            result = []
            for c in company:
                try:
                    data = self.get_indicators(c,span=span,period=period,kind=kind)
                    result.append(data)
                except:
                    pass
            return pd.concat(result)
        route = f"/technical_indicator/{span}/{company}?&type={kind}"
        json_data = self.get(route=route)
        data = pd.DataFrame(json_data)
        data["symbol"] = [company for _ in range(data.shape[0])]
        return data
        
        
            


def main():
    api = FinancialModelingPrep()
    data = api.get_stocklist()
    return 0

if __name__ == "__main__":
    main()