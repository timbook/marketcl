import yfinance as yf

def get_one_price(sym):
    df = yf.download(
        tickers=sym,
        period="5d",
        interval="1m",
        progress=False
    )
    return round(df.Close.dropna()[-1], 2)

def get_many_prices(syms):
    if isinstance(syms, str):
        return {syms.upper(): get_one_price(syms)}
    else:
        df = yf.download(tickers=syms, period="5d", interval="1m", progress=False)
        return {sym.upper() : df.Close[sym.upper()].dropna()[-1] for sym in syms.split()}

def color_picker(col):
    prefix = {
        "green": "\u001b[31m",
        "red": "\u001b[32m"
    }[col]
    return lambda s: prefix + s + "\u001b[0m"
