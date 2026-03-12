from __future__ import annotations

import argparse
import logging
import traceback

from analysis.dashboard import Dashboard
from analysis.logger import TradeLogger
from analysis.signalG import SignalGenerator
from capitalM.executionM import ExecutionManager
from capitalM.portfolioM import PortfolioManager
from capitalM.riskM import RiskManager
from data.candleD import CandleDataFetcher
from data.macroD import MacroDataFetcher
from data.tickD import TickDataFetcher


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def _run_stage(name: str, func, *args, **kwargs):
    try:
        logging.info("Stage start: %s", name)
        result = func(*args, **kwargs)
        logging.info("Stage complete: %s", name)
        return result
    except Exception as exc:
        logging.error("Stage failed: %s", name)
        logging.error("%s", traceback.format_exc())
        raise RuntimeError(f"Stage '{name}' failed: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trading pipeline")
    parser.add_argument("--mode", choices=["dev", "prod"], default="dev")
    parser.add_argument("--symbols", nargs="+", default=["EURUSD", "GBPUSD"])
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--candle-csv", default=None)
    parser.add_argument("--tick-csv", default=None)
    return parser.parse_args()


def main() -> None:
    _setup_logging()
    args = parse_args()

    macro_fetcher = MacroDataFetcher()
    candle_fetcher = CandleDataFetcher()
    tick_fetcher = TickDataFetcher()
    signal_gen = SignalGenerator()
    portfolio = PortfolioManager()
    risk = RiskManager()
    execution = ExecutionManager(mode=args.mode)
    logger = TradeLogger()
    dashboard = Dashboard()

    all_trades = []

    for symbol in args.symbols:
        macro_df = _run_stage(
            "load_macro",
            macro_fetcher.fetch_macro_data,
            args.symbols,
            args.mode,
        )
        candle_df = _run_stage(
            "load_candles",
            candle_fetcher.fetch_ohlc,
            symbol,
            args.count,
            args.mode,
            args.candle_csv,
        )
        ticks = _run_stage(
            "load_ticks",
            tick_fetcher.fetch_ticks,
            symbol,
            100,
            args.mode,
            args.tick_csv,
        )

        signals = _run_stage(
            "generate_signals",
            signal_gen.generate,
            macro_df,
            candle_df,
            ticks,
            symbol,
        )
        allocations = _run_stage("blend_allocations", portfolio.allocate, signals)
        risk_adjusted = _run_stage("risk_adjust", risk.apply, allocations, candle_df)
        orders = _run_stage("create_orders", execution.create_orders, risk_adjusted)
        trades = _run_stage("execute_orders", execution.execute, orders)
        all_trades.extend(trades)

    trades_df = _run_stage("log_trades", logger.record, all_trades)
    summary = _run_stage("dashboard", dashboard.summarize, trades_df)
    logging.info(summary)


if __name__ == "__main__":
    main()
