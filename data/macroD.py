from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Dict, Iterable, List

import requests
import pandas as pd


@dataclass(frozen=True)
class MacroConfig:
    countries: Dict[str, str]
    indicators: Dict[str, str]


class MacroDataFetcher:
    """
    Fetch macroeconomic indicators from the World Bank API.
    Returns a cleaned DataFrame with instrument, timestamp, and indicator columns.
    """

    def __init__(self, config: MacroConfig | None = None):
        if config is None:
            countries = {
                "USD": "US",
                "EUR": "EMU",  # Euro Area (can be flaky)
                "GBP": "GB",
                "JPY": "JP",
                "CHF": "CH",
                "CAD": "CA",
                "AUD": "AU",
                "NZD": "NZ",
            }
            indicators = {
                "GDP": "NY.GDP.MKTP.CD",
                "CPI": "FP.CPI.TOTL",
                "UnemploymentRate": "SL.UEM.TOTL.ZS",
                "TradeBalance": "NE.RSB.GNFS.CD",
            }
            config = MacroConfig(countries=countries, indicators=indicators)
        self.config = config

    def fetch_macro_data(self, currencies: Iterable[str], mode: str = "prod") -> pd.DataFrame:
        if not currencies:
            raise ValueError("currencies must be a non-empty iterable")
        if mode not in {"dev", "prod"}:
            raise ValueError("mode must be 'dev' or 'prod'")

        if mode == "dev":
            now = datetime.now(UTC)
            rows = []
            for ccy in currencies:
                rows.append(
                    {
                        "instrument": ccy,
                        "timestamp": now,
                        "GDP": 1.5,
                        "CPI": 2.1,
                        "UnemploymentRate": 4.2,
                        "TradeBalance": 0.3,
                    }
                )
            return pd.DataFrame(rows)

        df = self._fetch_worldbank(list(currencies))
        return self._clean_dataframe(df)

    def _safe_request(self, url: str, retries: int = 3, delay: int = 5) -> dict | None:
        """Perform a GET request with retries and exponential backoff."""
        for attempt in range(retries):
            try:
                resp = requests.get(url, timeout=20)
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, json.JSONDecodeError) as exc:
                if attempt < retries - 1:
                    time.sleep(delay * (attempt + 1))
                    continue
                print(f"⚠️ Skipping URL after failures: {url} ({exc})")
                return None

    def _fetch_worldbank(self, currencies: List[str]) -> pd.DataFrame:
        year_now = datetime.now(UTC).year
        end_year = year_now - 1
        start_year = end_year - 1

        rows = []
        for ccy in currencies:
            if ccy not in self.config.countries:
                raise ValueError(f"Unsupported currency: {ccy}")
            country = self.config.countries[ccy]

            series = {}
            for name, code in self.config.indicators.items():
                url = (
                    f"https://api.worldbank.org/v2/country/{country}/indicator/{code}"
                    f"?date={start_year}:{end_year}&format=json&per_page=200"
                )
                payload = self._safe_request(url)
                if not payload or not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
                    continue

                data = payload[1]
                for entry in data:
                    year = entry.get("date")
                    value = entry.get("value")
                    if year is None or value is None:
                        continue
                    key = str(year)
                    series.setdefault(key, {})[name] = float(value)

            for year, values in series.items():
                rows.append(
                    {
                        "instrument": ccy,
                        "timestamp": pd.Timestamp(f"{year}-12-31"),
                        "GDP": values.get("GDP"),
                        "CPI": values.get("CPI"),
                        "UnemploymentRate": values.get("UnemploymentRate"),
                        "TradeBalance": values.get("TradeBalance"),
                    }
                )

        if not rows:
            raise RuntimeError("No macro data returned from World Bank API")

        df = pd.DataFrame(rows).sort_values(["instrument", "timestamp"])
        return df
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle NaNs: forward-fill GDP/TradeBalance, interpolate CPI/Unemployment, then replace remaining NaNs with 0."""
        df = df.sort_values(["instrument", "timestamp"])

        # Forward-fill GDP and TradeBalance
        df[["GDP", "TradeBalance"]] = (
            df.groupby("instrument")[["GDP", "TradeBalance"]].transform(lambda g: g.ffill())
    )

        # Interpolate CPI and UnemploymentRate
        df[["CPI", "UnemploymentRate"]] = (
            df.groupby("instrument")[["CPI", "UnemploymentRate"]].transform(lambda g: g.interpolate())
    )

        # Final safeguard: replace any remaining NaNs with 0
        df = df.fillna(0)

        return df


if __name__ == "__main__":
    # Ensure pandas prints the full DataFrame
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)

    fetcher = MacroDataFetcher()
    df = fetcher.fetch_macro_data(
        ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"], mode="prod"
    )

    # Print the full cleaned DataFrame
    print(df.to_string())
