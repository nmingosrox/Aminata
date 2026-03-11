from data import macroD, candleD, tickD
from analysis.signalG import SignalGenerator
from analysis.logger import TradeLogger
from analysis.dashboard import Dashboard
from capitalM.riskM import RiskManager
from capitalM.portfolioM import PortfolioManager
from capitalM.executionM import ExecutionManager

import time

def main():
    """
    Main function to run the algorithmic trading bot.
    Initializes all modules and runs the main trading loop.
    """
    # Initialize modules
    sg = SignalGenerator(macro_source=macroD, candle_source=candleD, tick_source=tickD)
    rm = RiskManager()
    pm = PortfolioManager(capital=100000)
    exec_mgr = ExecutionManager()
    log = TradeLogger()
    dash = Dashboard()

    # Connect execution manager (MT5 placeholder)
    exec_mgr.connect()

    # Example loop (replace with scheduler or event-driven later)
    for cycle in range(3):  # run 3 cycles for testing
        print(f"\n--- Cycle {cycle+1} ---")

        # 1. Generate signals
        signals = sg.generate(symbols=["EURUSD", "GBPUSD"])
        print("Signals:", signals)

        # 2. Portfolio allocation
        allocations = pm.allocate(signals, weights={'macro':0.4,'calendar':0.3,'technical':0.3})
        print("Allocations:", allocations)

        # 3. Risk-adjusted sizing
        sized_positions = {}
        for sym, conviction in allocations.items():
            price_series = sg.get_price_series(sym)
            # Risk manager determines lot size based on conviction, capital, and volatility
            sized_positions[sym] = rm.position_size(
                symbol=sym,
                conviction=conviction,
                capital=pm.capital,
                price_series=price_series
            )
        print("Sized Positions:", sized_positions)

        # 4. Execution
        executed_trades = exec_mgr.rebalance(sized_positions)

        # 5. Logging
        for trade in executed_trades:
            entry_price = trade.get("price", 0.0)
            log.log_trade(trade.get("symbol", ""), entry_price, entry_price, 0.0, trade.get("timestamp"))

        # 6. Dashboard update
        dash.update(exec_mgr.closed_trades)

        time.sleep(1)  # simulate wait between cycles

    # Shutdown execution manager
    exec_mgr.shutdown()

if __name__ == "__main__":
    main()
