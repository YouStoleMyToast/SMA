#!/usr/bin/env python3
import numpy as np
import pandas as pd 
import time
from api_handler import FinancialModelingPrep as FMP


API = FMP()

class Monitor():
    def __init__(self,target_data):
        target_data = target_data[target_data["entryPrice"] > 0]
        target_data = target_data[target_data["exitPrice"] > 0]
        target_data = target_data[target_data["potentialGain"] > 0]
        self.TargetData = target_data
        self.CurrentData = target_data
        return

    def Notify(self,name,data):
        print("Notify")
        print(name)
        print(data)
        return

    def run(self):
        symbols = self.TargetData.symbol.to_list()
        while True:
            current_data = API.get_quote(symbols)
            current_distances = []
            for symbol in symbols:
                try:
                    current_price = current_data[current_data.symbol == symbol].price.iloc[-1]
                    current_distances.append({
                        "symbol":symbol,
                        "currentPrice":current_price,
                        "distanceFromTargetBuy": current_price - self.TargetData[self.TargetData.symbol == symbol].entryPrice.iloc[-1],
                        "percentFromTargetBuy":  1 - self.TargetData[self.TargetData.symbol == symbol].entryPrice.iloc[-1] / current_price,
                        "distanceFromTargetSell": self.TargetData[self.TargetData.symbol == symbol].exitPrice.iloc[-1] - current_price,
                        "percentFromTargetSell":  current_price / self.TargetData[self.TargetData.symbol == symbol].exitPrice.iloc[-1],
                    })
                except Exception as e:
                    print("Monitor Exception",e)
            current_distances = pd.DataFrame(current_distances)
            buy_distances = current_distances.sort_values("percentFromTargetBuy",ascending=False,axis=0).iloc[0:25]
            sell_distances = current_distances.sort_values("percentFromTargetSell",ascending=False,axis=0).iloc[0:25]
            buy_distances = pd.merge(self.TargetData,buy_distances,left_on="symbol",right_on="symbol")
            sell_distances = pd.merge(self.TargetData,sell_distances,left_on="symbol",right_on="symbol")
            self.Notify("BestBuys",buy_distances)
            self.Notify("BestSells",buy_distances)
            time.sleep(60)
        



def main():
    target_data = pd.read_csv("./data/calculatedTargetPricesVolatility.csv")
    monitor = Monitor(target_data)
    monitor.run()
    return

if __name__ == "__main__":
    main()