"""
Macro and calendar data utilities.
"""
from typing import Any, Dict, List
import pandas as pd
import requests

class MacroDataFetcher:
    """
    Fetch macroeconomic indicators from the World Bank API.
    """

    def fetch_macro_data(
        self,
        countries: list = ['EMU', 'GB', 'JP', 'CH', 'CA', 'AU', 'NZ', 'US'],
        indicators: dict = {
            'GDP': 'NY.GDP.MKTP.CD',
            'CPI': 'FP.CPI.TOTL',
            'Unemployment': 'SL.UEM.TOTL.ZS',
            'TradeBalance': 'NE.RSB.GNFS.CD'
        }
    ) -> pd.DataFrame:
        """
        Fetch macro data for multiple countries and indicators.
        Only returns the past 2 years of data.

        Returns:
            pd.DataFrame: Multi-index DataFrame with [date, country] as index
                          and indicators as columns.
        """
        all_data = []
        current_year = pd.Timestamp.today().year - 1
        start_year = current_year - 3

        for country in countries:
            dfs = []
            for name, code in indicators.items():
                # Restrict request to past 2 years
                url = (
                    f"http://api.worldbank.org/v2/country/{country}/indicator/{code}"
                    f"?date={start_year}:{current_year}&format=json&per_page=500"
                )
                r = requests.get(url)
                response = r.json()
                if len(response) < 2 or response[1] is None:
                    continue
                data = response[1]
                df = pd.DataFrame(data)[["date", "value"]].dropna()
                df["date"] = pd.to_datetime(df["date"], format="%Y")
                df = df.set_index("date").sort_index()
                df.rename(columns={"value": name}, inplace=True)
                dfs.append(df)

            if dfs:
                country_df = pd.concat(dfs, axis=1)
                country_df["Country"] = country
                all_data.append(country_df)

        if not all_data:
            return pd.DataFrame()

        result = pd.concat(all_data)
        result = result.reset_index().set_index(["date", "Country"])
        return result


if __name__ == "__main__":
    fetcher = MacroDataFetcher()
    df = fetcher.fetch_macro_data()
    print(df.head())
    print(df.tail())
