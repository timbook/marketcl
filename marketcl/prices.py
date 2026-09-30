"""Price lookups from Yahoo Finance (via the yfinance package)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Iterable, Optional


class PriceError(Exception):
    pass


def get_price(symbol: str) -> float:
    """Return the latest price for a symbol, or raise PriceError."""
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover
        raise PriceError("The 'yfinance' package is not installed.") from exc

    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)

        price: Optional[float] = None
        try:
            price = ticker.fast_info["last_price"]
        except Exception:
            price = None

        if price is None or price != price or price <= 0:  # None / NaN / bad
            history = ticker.history(period="5d")
            closes = history["Close"].dropna()
            if closes.empty:
                raise PriceError(f"No price data found for '{symbol}'.")
            price = float(closes.iloc[-1])

        return round(float(price), 2)
    except PriceError:
        raise
    except Exception as exc:
        raise PriceError(f"Could not fetch a price for '{symbol}': {exc}") from exc


def get_prices(symbols: Iterable[str]) -> Dict[str, Optional[float]]:
    """Fetch several prices in parallel. Failed lookups map to None."""
    symbols = list(symbols)
    if not symbols:
        return {}

    def fetch(sym: str) -> Optional[float]:
        try:
            return get_price(sym)
        except PriceError:
            return None

    with ThreadPoolExecutor(max_workers=min(8, len(symbols))) as pool:
        return dict(zip(symbols, pool.map(fetch, symbols)))
