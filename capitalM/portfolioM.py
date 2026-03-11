class PortfolioManager:
    """
    PortfolioManager is responsible for capital allocation. It blends signals
    from the SignalGenerator into a final conviction score and determines the
    target allocation for each asset in the portfolio.
    """
    def __init__(self, capital=100000):
        """
        Initializes the PortfolioManager.
        Args:
            capital (float): The total trading capital available.
        """
        self.capital = capital

    def allocate(self, signals, weights=None):
        """
        Blend signals into target allocations using a weighted formula.
        The output is a conviction score for each symbol.

        Args:
            signals (dict): A dictionary of signals per symbol.
            weights (dict): Weights for each signal type (macro, calendar, technical).

        Returns:
            dict: A dictionary mapping symbols to their final blended conviction score.
        """
        allocations = {}
        for sym, signal_values in signals.items():
            score = (weights.get('macro', 0) * signal_values.get('macro', 0) +
                     weights.get('calendar', 0) * signal_values.get('calendar', 0) +
                     weights.get('technical', 0) * signal_values.get('technical', 0))
            allocations[sym] = score
        return allocations
