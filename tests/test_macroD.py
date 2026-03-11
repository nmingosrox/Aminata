import pandas as pd
import numpy as np

from .data.macroD import MacroDataFetcher


def _assert_numeric(df, columns):
    for col in columns:
        series = pd.to_numeric(df[col].dropna(), errors="coerce")
        assert not series.empty
        assert np.isfinite(series).all()


def test_worldbank_macro_fetcher():
    fetcher = MacroDataFetcher()
    df = fetcher.fetch_all()

    assert not df.empty

    for country in fetcher.countries:
        expected_cols = [
            f"{country}_GDP",
            f"{country}_CPI",
            f"{country}_Unemployment",
            f"{country}_TradeBalance",
        ]
        for col in expected_cols:
            assert col in df.columns
        _assert_numeric(df, expected_cols)

    print(df.tail())

if __name__ == "__main__":
    test_worldbank_macro_fetcher()
