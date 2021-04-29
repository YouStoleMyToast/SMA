import time
FINANCIAL_MODELING_PREP_API_TOKENS =[ ] 


markets = ['New York Stock Exchange','Nasdaq']
# markets = ['NYSE','Nasdaq']
API_VERBOSE = True



###################
# ARBITRAGE MODEL #
###################
ARB_VERBOSE = False
arbitrage_array_size_limit = 60 # the rate at which data is store will coorelate with the fetch interval
arbitrage_sudden_change_time_limit = 20 #gets computed as the coefficient to the array size limit; assume data in the arrays are updated every second
arbitrage_fetch_interval = 5 # how many seconds to wait between api calls
arbitrage_sudden_ratio_limit = arbitrage_sudden_change_time_limit / arbitrage_array_size_limit
def new_score():
    return  {
            "sudden_negative_score" : 0, # the number of stocks that have changed negatively under the time ratio
            "sudden_positive_score" : 0, # the number of stocks that have changed positively under the time ratio
            "overall_score"         : 0, #sum of time ratios and their direction; ultimately determines the direction the market has most recently changed
            "datetime"              : time.time()
        } 
