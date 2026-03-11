from data.macroD import MacroDataFetcher as mdf

macro = mdf()
m = macro.fetch_macro_data()

print(m)