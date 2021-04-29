#!/usr/bin/env python3
import numpy as np
import pandas as pd
import time,datetime
import os, sys
import argparse

from api_handler import FinancialModelingPrep as FMP 

from config import arbitrage_array_size_limit as SIZE_LIMIT
from config import arbitrage_sudden_change_time_limit as TIME_LIMIT
from config import arbitrage_fetch_interval as FETCH_INTERVAL
from config import arbitrage_sudden_ratio_limit as SUDDEN_RATIO_LIMIT
from config import new_score
from config import ARB_VERBOSE as VERBOSE

API = FMP()
verbose = VERBOSE

def change_percent(old_value,new_value):
    return (new_value - old_value) / old_value


class StatisticalArbitrageModel():
    def __init__(self,test=False):
        self.stocklist = ["BA","AAPL","GOOGL","MSFT","AMZN","FB","T","SQ","BAC","TSLA"] # I should run an algorithm to find stocks with the best coorelation to the market; at a later date
        self.history = pd.read_csv("./data/arbitrage_history.csv")
        self.price_data = [ [] for _ in range(len(self.stocklist)) ]
        self.change_data = [ [] for _ in range(len(self.stocklist)) ]
        self.score_data = [ [] for _ in range(len(self.stocklist)) ]
        self.ratio_statuses = [ (0,0) for _ in range(len(self.stocklist)) ]
        if test:
            self.init_test()
        print("Starting")
        return 

    def __del__(self):
        # self.history.to_csv('./data/arbitrage_history.csv',index=0)
        return

    def init_test(self):
        print("Initializing Test")
        self.test = True
        self.test_data = pd.read_csv("../test_data.csv")
        self.test_data["symbol"] = [ self.stocklist[int(row["symbol"])] for index,row in self.test_data.iterrows() ]
        self.current_iteration = 1
        return 

    def get_test(self):
        if self.current_iteration > max(self.test_data["iteration"].astype(int).unique()):
            print("Test Completed")
            exit(0)
        data = self.test_data[self.test_data["iteration"] == self.current_iteration]
        self.current_iteration += 1
        return data


    def update(self):
        if self.test:
            data = self.get_test()
        else:
            data = API.get_quote(self.stocklist)
        prices = data.price.to_list()
        for i in range(len(self.price_data)):
            self.price_data[i].append(prices[i])
            if len(self.price_data[i] ) > 1:
                change = change_percent(self.price_data[i][len(self.price_data[i])-2],self.price_data[i][len(self.price_data[i])-1])
                self.change_data[i].append(change)
        return

    def evaluate(self):
        if len(self.change_data[0]) < 2:
            return 0
        for i in range(len(self.change_data)):
            if self.change_data[i][len(self.change_data[i])-2] > 0 and self.change_data[i][len(self.change_data[i])-1] < 0:
                self.score_data[i].append(-1)
            elif self.change_data[i][len(self.change_data[i])-2] < 0 and self.change_data[i][len(self.change_data[i])-1] > 0:
                self.score_data[i].append(1)
            else:
                self.score_data[i].append(0)
        return 


    def update_status(self):
        for k in range(len(self.score_data)):
            scores = self.score_data[k] #renaming
            for i in range(len(scores)-1,0,-1):
                if abs(scores[i]) == 1: #if the score has not changed, the status of the stock will not change at all
                    time_ratio = (len(scores)-i-1) / SIZE_LIMIT # #Compared to the size limit of the lists which is ultimately 60 seconds if it sleeps for 1 minute between calls (evaluate)
                    self.ratio_statuses[k] = (time_ratio,scores[i])
                    break
        return 

    def score(self):
        self.update_status()
        if len(self.score_data[0]) < TIME_LIMIT:
            return False        
        scores = new_score()

        for x in range(len(self.ratio_statuses)):
            time_ratio,direction = self.ratio_statuses[x]
            scores["overall_score"] += time_ratio * direction #add time ratio as a positive or negative value
            if time_ratio < SUDDEN_RATIO_LIMIT:
                if direction < 0:
                    scores["sudden_negative_score"] += 1
                elif direction > 0:
                    scores["sudden_positive_score"] += 1
                    
        return scores

            
            
    def notify(self,data,emergency=False): #data is message if emergency is true; otherwise a dict
        if emergency:
            print("Emergency Alert")
            print(data)
            return
        print("Basic Alert")
        print(data)
        return 

    def cleanup(self):
        if len(self.score_data[0]) > SIZE_LIMIT:
            diff = len(self.score_data[0]) - SIZE_LIMIT
            for i in range(len(self.score_data)):
                self.price_data[i]  =    self.price_data[i][diff:]
                self.change_data[i] =    self.change_data[i][diff:]
                self.score_data[i]  =    self.score_data[i][diff:]
        return


    def evaluate_scores(self,scores):
        if scores[ "overall_score" ] < 0 or scores[ "sudden_negative_score" ] > 4 or scores[ "sudden_positive_score" ] > 6:
            self.notify(pd.DataFrame(scores,index=[0]),emergency=True)
        elif verbose:
            print("No Notify\n" , pd.DataFrame(scores,index=[0]) , "\n---------------")
        print() if verbose else None
        return

    def execute(self):
        self.update()
        self.evaluate()
        scores = self.score()
        if not scores:
            print("Standby.. " + str(TIME_LIMIT - len(self.score_data[0]))) if verbose else None
            return 
        self.evaluate_scores( scores )
        self.history.append( scores , ignore_index=True )
        self.cleanup()
        return 


    def run(self):
        self.update()
        consecutive_exceptions = 0
        next_save = datetime.datetime.now() + datetime.timedelta(minutes=1)
        while True:

            if datetime.datetime.now() >= next_save:
                self.history.to_csv("./data/arbitrage_history.csv",index=0)
                next_save = datetime.datetime.now() + datetime.timedelta(minutes=1)
            time.sleep( FETCH_INTERVAL )

            try:
                self.execute() # Everything other line except this one in the while loop is padding 
                consecutive_exceptions = 0
            except Exception as e:
                print("Exception Has Occured",e)
                self.history.to_csv('./data/arbitrage_history.csv',index=0)
                consecutive_exceptions += 1
                if consecutive_exceptions > 5:
                    self.notify("The Preceeding Exception Has Occured Consecutively " + str(consecutive_exceptions) + " times.",emergency=True)
                    time.sleep(600)

        return 


parser = argparse.ArgumentParser(prog="Statistical Arbitrage Model",description="This model is designed to monitor sudden changes in the stock market by tracking influential stocks")
parser.add_argument("--test",default=False,choices=["True","False"],help="Simulate Run With Test Data")
parser.add_argument("--verbose",default=False,choices=["True","False"],help="Print Helpful Data While Running")

def main():
    args = parser.parse_args()
    verbose = args.verbose
    model = StatisticalArbitrageModel(test=args.test)
    data = model.run()
    # print(data)
    return 0

if __name__ == "__main__":
    main()

