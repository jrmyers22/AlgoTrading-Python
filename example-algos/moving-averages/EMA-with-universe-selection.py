class EMAMomentumUniverse(QCAlgorithm):
    
    def Initialize(self):
        self.SetStartDate(2016, 1, 7)
        self.SetEndDate(2021, 1, 7)
        self.SetCash(100000)
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction) 
        self.averages = {}
        self._changes = None
    
    # "First Pass" filtering on highest DollarVolume and whether security has FundamentalData available
    # Narrows the universe down to 10 securities which have 50 day moving averages greater than 200 day
    def CoarseSelectionFunction(self, universe):  
        selected = []
        universe = sorted(universe, key=lambda c: c.DollarVolume, reverse=True)  
        universe = [ x for x in universe if x.HasFundamentalData ][:100]

        for coarse in universe:  
            symbol = coarse.Symbol
            
            if symbol not in self.averages:
                # Call history to get an array of 200 days of history data
                history = self.History(symbol, 200, Resolution.Daily)
                
                # Add security to dict as SelectionData obj
                self.averages[symbol] = SelectionData(history) 

            # Update the indicator with Adjusted Price (account for splits and dividends)
            self.averages[symbol].update(self.Time, coarse.AdjustedPrice)
            
            #TODO: Need to move this logic to OnData instead of in Universe Selection
            if self.averages[symbol].is_ready() and self.averages[symbol].fast > self.averages[symbol].slow:
                selected.append(symbol)
        
        return selected[:10]
        
    # This event fires whenever we have changes to our universe
    def OnSecuritiesChanged(self, changes):
        self._changes = changes
        self.Log(f"OnSecuritiesChanged({self.UtcTime}):: {changes}")
        for security in changes.RemovedSecurities:
            self.Liquidate(security.Symbol)
       
        for security in changes.AddedSecurities:
            self.SetHoldings(security.Symbol, 0.10)
            
    # This even fires whenever an order is placed
    def OnOrderEvent(self, fill):
        self.Log(f"OnOrderEvent({self.UtcTime}):: {fill}") 
            
class SelectionData():
    def __init__(self, history):
        self.slow = SimpleMovingAverage(200)
        self.fast = SimpleMovingAverage(50)
        
        # Loop over the history data and update the indicators
        for bar in history.itertuples():
            self.fast.Update(bar.Index[1], bar.close)
            self.slow.Update(bar.Index[1], bar.close)
    
    def is_ready(self):
        return self.slow.IsReady and self.fast.IsReady
    
    def update(self, time, price):
        self.fast.Update(time, price)
        self.slow.Update(time, price)
  

