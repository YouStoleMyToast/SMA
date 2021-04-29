#!/usr/bin/env python3
import os, sys

if not "data" in os.listdir("./"):
    os.mkdir("./data")




















print("\n" * 30)
print("\nCopy The Following Lines Into Terminal/Console (If you did not run the Makefile)\n")
print("python3 -m pip install -r requirements.txt")
print("chmod +x *.py")

print("\n" * 3 + "Sample File Runs")
print("-" * 50)
print("./PlotStocks.py")
print("./ProcessData.py")
print("./Run.py genplots=1 savePlot=1 showPlot=0 verbose=0")

print("\n" * 3 + "Import The ProcessedData Library and Use It\n" + "-" * 50)
print("import datetime\nimport numpy as np\nimport pandas as pd")
print("from ProcessData import ProcessedDataLibrary as PDL")
print("\nlib = PDL()")
print("\nupTo = datetime.datetime(2020,1,1) #optional")
print("days = datetime.timedelta(200) #optional")
print("\ndata = lib.get(\"AAPL\",upTo,days)\nprint(data)\n")
print("-" * 50)

