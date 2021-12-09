from AlphaModel import *
import random

class SmoothMagentaOwl(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2015, 1, 1)  # Set Start Date
        self.SetEndDate(2018, 6, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        
        # Compare to the SPY chart
        self.SetBenchmark("SPY")
        
        # 500 securities sent to Fine Filter, 5 output from Fine
        self.num_coarse = 500
        self.count = 5
        self.activeStocks = []
        self._changes = None
        
        # Small-Cap stock definition defined by Investopedia (300M - 2B)
        # https://www.investopedia.com/terms/s/small-cap.asp
        self.smallCapLowerBound = 300000000.0 # 300 million
        self.smallCapUpperBound = 2000000000.0 # 2 billion
        
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        
        # Alpha Model
        self.AddAlpha(EmaCrossAlphaModel())
        
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())
        self.SetExecution(ImmediateExecutionModel())
        
    def CoarseSelectionFunction(self, coarse):
        
        # Only rebalance Universe every 5 days
        if self.Time.day % 5 != 0:
            return Universe.Unchanged
        
        # Select only those with fundamental data and a sufficiently large price
        # Sort by top dollar volume: most liquid to least liquid
        selected = sorted([x for x in coarse if x.HasFundamentalData and x.Price > 5],
                            key = lambda x: x.DollarVolume, reverse=True)

        return [x.Symbol for x in selected[:self.num_coarse]]


    def FineSelectionFunction(self, fine):
        # Selects 5 random Small-Cap stocks
        small_market_cap = [x for x in fine if x.MarketCap > self.smallCapLowerBound and x.MarketCap < self.smallCapUpperBound]
        random.shuffle(small_market_cap)
        
        return [x.Symbol for x in small_market_cap[:self.count]]

    def OnData(self, data):
        # if we have no changes, do nothing
        if self._changes is None: return
    
        # liquidate removed securities
        for security in self._changes.RemovedSecurities:
            if security.Invested:
                self.Liquidate(security.Symbol)

        # we want 1/N allocation in each security in our universe
        for security in self._changes.AddedSecurities:
            self.SetHoldings(security.Symbol, 1 / self.count)

        self._changes = None
    
    
