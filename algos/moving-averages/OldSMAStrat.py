from AlgorithmImports import *
from System.Collections.Generic import List

# Leverage SimpleMovingAverage Indicator
# 100% entry and exit points based on 50 and 200 day moving averages
#   - Buy 100% when 50 day is higher than 200 day
#   - Sell 100% when 50 day is lower than 200 day
# 25% entry and exit based on 10 and 50 day moving averages
#   - Buy 25% of available capital if 10 day is higher than 50 day
#   - Sell 25% of available capital if 10 day is lower than 50 day
# - Sell 5% for every 10% gain
# - Sell 5% for every 15% drop
class OldSMAStrat(QCAlgorithm):

    def Initialize(self):
        '''Initialise the data and resolution required, as well as the cash and start-end dates for your algorithm. All algorithms must initialized.'''

        self.SetStartDate(2020,11,9)  #Set Start Date
        self.SetEndDate(2021,11,9)    #Set End Date
        self.SetCash(100000)         #Set Strategy Cash
        self.UniverseSettings.Resolution = Resolution.Daily
        
        # Set BND Benchmark
        self.SetBenchmark("SPY")
        
        # Add to our portfolio
        self.AddEquity("SPY", Resolution.Daily)
        
        # Set the 200/50/10 day simple moving average indicators for SPY
        self.spySMATen = self.SMA("SPY", 10, Resolution.Daily) 
        self.spySMAFifty = self.SMA("SPY", 50, Resolution.Daily) 
        self.spySMATwoHund = self.SMA("SPY", 200, Resolution.Daily) 
        
        # Set the Rate Of Change Percent Indicator for the last 1 day
        self.spyROCPOne = self.ROCP("SPY", 1, Resolution.Daily)
        
        # Warm up algorithm for 200 days to populate the indicators prior to the start date
        self.SetWarmUp(200)

    def OnData(self, data):
        # Validate indicators exist and are ready before using them
        indicatorsExist = self.spySMATen is not None and self.spySMAFifty is not None and self.spySMATwoHund is not None and self.spyROCPOne is not None
        indicatorsReady = self.spySMATen.IsReady and self.spySMAFifty.IsReady and self.spySMATwoHund.IsReady and self.spyROCPOne.IsReady
        if not indicatorsExist or not indicatorsReady:
            return
        
        # If 50 day is higher than 200 day, then we allocate 100% of our Buying Power to SPY
        if self.spySMAFifty.Current.Value > self.spySMATwoHund.Current.Value:
            self.SetHoldings("SPY", 1)
        else:
            # Free up 100% of our buying power (sell all shares)
            self.Liquidate("SPY")
            
        # If 10 day is higher than 50 day, allocate 25% of buying power to SPY    
        if self.spySMATen.Current.Value > self.spySMAFifty.Current.Value:
            self.SetHoldings("SPY", 0.25)
        else:
            # Sell 25% of SPY holdings:
            #   Get num SPY holdings / 25
            #   Put in MarketOrder for negative that many
            quarterOfSPYHoldings = int(self.Securities["SPY"].Holdings.Quantity * 0.25)
            self.MarketOrder("SPY", -quarterOfSPYHoldings)
        
        # Sell 5% for every 10(ish) % gain
        if 10.0 <= self.spyROCPOne.Current.Value <= 10.5:
            quarterOfSPYHoldings = int(self.Securities["SPY"].Holdings.Quantity * 0.05)
            self.MarketOrder("SPY", -quarterOfSPYHoldings)
        # Sell 5% for every 15(ish) % drop
        elif -15.5 <= self.spyROCPOne.Current.Value <= -15.0:
            quarterOfSPYHoldings = int(self.Securities["SPY"].Holdings.Quantity * 0.05)
            self.MarketOrder("SPY", -quarterOfSPYHoldings)
            
