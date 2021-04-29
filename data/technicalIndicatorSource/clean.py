#!/usr/bin/env python3
import os, sys
import datetime 

import numpy as np
import pandas as pd 


def cleanIndicatorData():
    for f in os.listdir("./"):
        if f.count("_"):
            try:
                date = f.split("_")[1].split(".")[0]
                year,month,day = date.split("-")
                date = datetime.datetime(int(year),int(month),int(day))
                if datetime.datetime.now() - date > datetime.timedelta(days=7):
                    print("removed\t",f)
                    os.remove("./" + f)
            except Exception as e:
                print(e)
                continue


def main():
    cleanIndicatorData()

if __name__ == "__main__":
    main()
