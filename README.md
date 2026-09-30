# marketcl

A command line paper trading game for the stock market. Prices come from Yahoo Finance.

## Install (local)

```bash
cd marketcl
pip install -e .
```

This installs two identical commands: `marketcl` and `mcl`.

## Commands

| Command | What it does |
|---|---|
| `mcl new [name]` | Create a game (prompts for initial capital, default $10,000) and switch to it |
| `mcl game [name]` | Switch games (shows a numbered picker if no name given) |
| `mcl list` / `mcl l` | Pretty table of holdings, cash, and total P/L |
| `mcl buy [XYZ]` / `mcl b` | Buy shares at the live price (prompts for symbol if omitted, then quantity; shows total cost, asks to confirm) |
| `mcl sell [XYZ]` / `mcl s` | Sell shares at the live price (prompts for symbol if omitted, then quantity; shows proceeds + realized P/L) |

Trades always execute at the live Yahoo Finance price. The price is shown to you but can't be
edited; you only choose the quantity.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Data

Everything is stored as JSON in `~/.mcl`:

```
~/.mcl/config.json          # which game is active
~/.mcl/games/<name>.json    # one file per game (cash, holdings, transaction log)
```

Set `MCL_HOME` to use a different directory (handy for testing).
