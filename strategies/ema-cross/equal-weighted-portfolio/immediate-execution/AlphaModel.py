class EmaCrossAlphaModel(AlphaModel):
    
    def __init__(self,
                 fastPeriod = 5,
                 slowPeriod = 25,
                 resolution = Resolution.Daily):
        '''Initializes a new instance of the EmaCrossAlphaModel class
        Args:
            fastPeriod: The fast EMA period
            slowPeriod: The slow EMA period'''
        self.fastPeriod = fastPeriod
        self.slowPeriod = slowPeriod
        self.resolution = resolution
        self.predictionInterval = 5
        
        self.insightSymbol = None
        self.insightPrice = None
        self.insightInterval = None
        self.insightDirection = None
        
        self.symbolDataBySymbol = {}
        self._insights = []

    def Update(self, algorithm, data):
        '''Updates this alpha model with the latest data from the algorithm.
        This is called each time the algorithm receives data for subscribed securities
        Args:
            algorithm: The algorithm instance
            data: The new data available
        Returns:
            New insights'''
        
        insights = []
        
        for symbol, symbolData in self.symbolDataBySymbol.items():
            if symbolData.fastEMA.IsReady and symbolData.slowEMA.IsReady:
                
                algorithm.Debug("25 day: " + str(symbolData.slowEMA.Current.Value))
                algorithm.Debug("5 day: " + str(symbolData.fastEMA.Current.Value))
                
                if symbolData.slowEMA.Current.Value > symbolData.fastEMA.Current.Value:
                    algorithm.Debug(str(symbol) + " Slow > Fast, Insight Down (sell/short) ")
                    self.insightSymbol = symbolData.Symbol
                    self.insightInterval = self.predictionInterval
                    self.insightDirection = InsightDirection.Down
                    self.insightPrice = Insight.Price(symbolData.Symbol, timedelta(days=self.predictionInterval), InsightDirection.Down)
                    insights.append(self.insightPrice)
    
                elif symbolData.slowEMA.Current.Value < symbolData.fastEMA.Current.Value:
                    algorithm.Debug(str(symbol) + " Fast > Slow, Insight Up (sell/short) ")
                    self.insightSymbol = symbolData.Symbol
                    self.insightInterval = self.predictionInterval
                    self.insightDirection = InsightDirection.Up
                    self.insightPrice = Insight.Price(symbolData.Symbol, timedelta(days=self.predictionInterval), InsightDirection.Up)
                    insights.append(self.insightPrice)
    
        self._insights = insights
        return insights

    def OnSecuritiesChanged(self, algorithm, changes):
        '''Event fired each time the we add/remove securities from the data feed
        Args:
            algorithm: The algorithm instance that experienced the change in securities
            changes: The security additions and removals from the algorithm'''
        
        # Liquidate holdings of removed securities
        for removed in changes.RemovedSecurities:
            algorithm.Liquidate(removed.Symbol)
        
        # Save all newly added securities
        for added in changes.AddedSecurities:
            algorithm.Debug("Added Security: " + str(added.Symbol))
            
            symbolData = self.symbolDataBySymbol.get(added.Symbol)
            if symbolData is None:
                symbolData = SymbolData(algorithm, added, self.slowPeriod, self.fastPeriod, self.resolution)
                self.symbolDataBySymbol[added.Symbol] = symbolData
            else:
                # a security that was already initialized was re-added, reset the indicators
                symbolData.Fast.Reset()
                symbolData.Slow.Reset()

class SymbolData:
    '''Contains data specific to a symbol required by this model'''
    def __init__(self, algorithm, security, slowPeriod, fastPeriod, resolution):
        self.Security = security
        self.Symbol = security.Symbol

        # True if the fast is above the slow, otherwise false.
        # This is used to prevent emitting the same signal repeatedly
        self.FastIsOverSlow = False
        
        # Create Slow EMA Indicator for Security
        slowEMA = algorithm.CreateIndicatorName(self.Symbol, f"EMA{slowPeriod}", resolution)
        self.slowEMA = ExponentialMovingAverage(slowEMA, slowPeriod)
        algorithm.RegisterIndicator(self.Symbol, self.slowEMA, resolution)

        # warmup our indicator by pushing history through the indicators
        history = algorithm.History(self.Symbol, slowPeriod, resolution)
        if 'close' in history:
            history = history.close.unstack(0).squeeze()
            for time, value in history.iteritems():
                self.slowEMA.Update(time, value)
                
        # Create Fast EMA Indicator for Security
        fastEMA = algorithm.CreateIndicatorName(self.Symbol, f"EMA{fastPeriod}", resolution)
        self.fastEMA = ExponentialMovingAverage(fastEMA, fastPeriod)
        algorithm.RegisterIndicator(self.Symbol, self.fastEMA, resolution)

        # warmup our indicator by pushing history through the indicators
        history = algorithm.History(self.Symbol, fastPeriod, resolution)
        if 'close' in history:
            history = history.close.unstack(0).squeeze()
            for time, value in history.iteritems():
                self.fastEMA.Update(time, value)

    @property
    def SlowIsOverFast(self):
        return not self.FastIsOverSlow
