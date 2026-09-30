"""Command line interface for marketcl (`marketcl` or `mcl`)."""
from __future__ import annotations

from datetime import datetime, timezone

import click
from rich import box
from rich.console import Console
from rich.table import Table

from . import __version__, storage
from .prices import PriceError, get_price, get_prices

console = Console()

DEFAULT_CAPITAL = 10000.0


# ------------------------------------------------------------- helpers

def money(value: float) -> str:
    return f"-${abs(value):,.2f}" if value < 0 else f"${value:,.2f}"


def colored_money(value: float) -> str:
    color = "green" if value > 0 else "red" if value < 0 else "white"
    sign = "+" if value > 0 else ""
    return f"[{color}]{sign}{money(value)}[/{color}]"


def colored_pct(value: float) -> str:
    color = "green" if value > 0 else "red" if value < 0 else "white"
    sign = "+" if value > 0 else ""
    return f"[{color}]{sign}{value:.2f}%[/{color}]"


def require_game() -> dict:
    game = storage.get_current_game()
    if game is None:
        raise click.ClickException(
            "No active game. Create one with 'mcl new' or pick one with 'mcl game'."
        )
    return game


def resolve_symbol(symbol):
    """Use the symbol given on the command line, or prompt for one."""
    while not symbol or not symbol.strip():
        symbol = click.prompt("Symbol", default="", show_default=False)
    symbol = symbol.strip().upper()
    if any(ch.isspace() for ch in symbol):
        raise click.ClickException(f"'{symbol}' is not a valid ticker symbol.")
    return symbol


def fetch_market_price(symbol: str) -> float:
    """Get the live Yahoo Finance price. This is the only price trades can use."""
    with console.status(f"Fetching price for {symbol}..."):
        try:
            return get_price(symbol)
        except PriceError as exc:
            raise click.ClickException(str(exc))


def log_transaction(game: dict, kind: str, symbol: str, qty: int, price: float, total: float, **extra) -> None:
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": kind,
        "symbol": symbol,
        "quantity": qty,
        "price": price,
        "total": round(total, 2),
    }
    entry.update(extra)
    game["transactions"].append(entry)


def print_order_summary(action, symbol, qty, price, total, total_label, cash_before, cash_after) -> None:
    table = Table(box=box.SIMPLE_HEAVY, show_header=False, title=f"{action} order summary")
    table.add_column(style="dim")
    table.add_column(justify="right")
    table.add_row("Symbol", f"[bold]{symbol}[/bold]")
    table.add_row("Quantity", f"{qty:,}")
    table.add_row("Market price", money(price))
    table.add_row(f"[bold]{total_label}[/bold]", f"[bold]{money(total)}[/bold]")
    table.add_row("Cash before", money(cash_before))
    table.add_row("Cash after", money(cash_after))
    console.print(table)


# --------------------------------------------------------------- group

class AliasedGroup(click.Group):
    """Adds short aliases (`mcl l`, `mcl b`, `mcl s`) and a trailing blank line."""

    aliases = {"l": "list", "b": "buy", "s": "sell"}

    def get_command(self, ctx, cmd_name):
        return super().get_command(ctx, self.aliases.get(cmd_name, cmd_name))

    def main(self, *args, **kwargs):
        # Always end output with an empty line so it doesn't butt up against the
        # next shell prompt. Covers normal output, errors, --help and Ctrl-C.
        try:
            return super().main(*args, **kwargs)
        finally:
            click.echo()


@click.group(cls=AliasedGroup, invoke_without_command=True)
@click.version_option(__version__, prog_name="marketcl")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """marketcl: paper trade the stock market from your terminal."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ------------------------------------------------------------ commands

@cli.command("new")
@click.argument("name", required=False)
def new_game(name):
    """Create a new game and switch to it."""
    console.print("[bold]Create a new game[/bold]")
    while True:
        if not name:
            name = click.prompt("Game name").strip()
        if not storage.slugify(name):
            console.print("[red]Name must contain letters or numbers.[/red]")
        elif storage.game_exists(name):
            console.print(f"[red]A game named '{name}' already exists.[/red]")
        else:
            break
        name = None

    capital = click.prompt(
        f"Initial capital [{money(DEFAULT_CAPITAL)}]",
        type=click.FloatRange(min=0, min_open=True),
        default=DEFAULT_CAPITAL,
        show_default=False,
    )

    game = storage.create_game(name, capital)
    storage.set_current_slug(game["slug"])
    console.print(
        f"[green]Created game '{game['name']}' with {money(game['initial_capital'])} "
        f"and switched to it.[/green]"
    )


@cli.command("game")
@click.argument("name", required=False)
def switch_game(name):
    """Switch between games."""
    games = storage.list_games()
    if not games:
        raise click.ClickException("No games yet. Create one with 'mcl new'.")

    current = storage.get_current_slug()

    if name:
        matches = [g for g in games if g["slug"] == storage.slugify(name)]
        if not matches:
            raise click.ClickException(f"No game named '{name}'.")
        chosen = matches[0]
    else:
        table = Table(box=box.ROUNDED, title="Your games")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Game", style="bold")
        table.add_column("Cash", justify="right")
        table.add_column("Started with", justify="right")
        table.add_column("Active", justify="center")
        for i, g in enumerate(games, 1):
            table.add_row(
                str(i),
                g["name"],
                money(g["cash"]),
                money(g["initial_capital"]),
                "[green]●[/green]" if g["slug"] == current else "",
            )
        console.print(table)

        default = next((i for i, g in enumerate(games, 1) if g["slug"] == current), 1)
        pick = click.prompt(
            "Switch to game #",
            type=click.IntRange(1, len(games)),
            default=default,
        )
        chosen = games[pick - 1]

    storage.set_current_slug(chosen["slug"])
    console.print(f"[green]Switched to '{chosen['name']}'.[/green]")


@cli.command("list")
def list_holdings():
    """List current holdings and cash (alias: l)."""
    game = require_game()
    holdings = game["holdings"]

    with console.status("Fetching prices..."):
        prices = get_prices(holdings.keys())

    table = Table(box=box.ROUNDED, title=game["name"], title_style="bold cyan")
    table.add_column("Symbol", style="bold")
    table.add_column("Shares", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Market Value", justify="right")
    table.add_column("P/L", justify="right")
    table.add_column("P/L %", justify="right")

    stocks_value = 0.0
    stale = []
    for symbol in sorted(holdings):
        pos = holdings[symbol]
        shares, avg = pos["shares"], pos["avg_cost"]
        price = prices.get(symbol)
        if price is None:
            stale.append(symbol)
            table.add_row(symbol, f"{shares:,}", money(avg), "[dim]n/a[/dim]", "[dim]n/a[/dim]", "", "")
            stocks_value += shares * avg  # fall back to cost basis
            continue
        value = shares * price
        cost = shares * avg
        pl = value - cost
        pl_pct = (pl / cost * 100) if cost else 0.0
        stocks_value += value
        table.add_row(
            symbol, f"{shares:,}", money(avg), money(price), money(value),
            colored_money(pl), colored_pct(pl_pct),
        )

    table.add_section()
    table.add_row("[bold]CASH[/bold]", "", "", "", money(game["cash"]), "", "")
    total = game["cash"] + stocks_value
    gain = total - game["initial_capital"]
    gain_pct = gain / game["initial_capital"] * 100
    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]", "", "", "", f"[bold]{money(total)}[/bold]",
        colored_money(gain), colored_pct(gain_pct),
    )
    console.print(table)
    console.print(
        f"Started with {money(game['initial_capital'])}  •  "
        f"Overall: {colored_money(gain)} ({colored_pct(gain_pct)})"
    )
    if stale:
        console.print(
            f"[yellow]Couldn't fetch prices for: {', '.join(stale)}. "
            f"Valued at cost for the total.[/yellow]"
        )


@cli.command("buy")
@click.argument("symbol", required=False)
def buy(symbol):
    """Buy shares of SYMBOL at the current Yahoo Finance price (alias: b).

    If SYMBOL is omitted you'll be prompted for it.
    """
    game = require_game()
    symbol = resolve_symbol(symbol)
    price = fetch_market_price(symbol)

    console.print(
        f"\n[bold]BUY {symbol}[/bold]  •  current price [cyan]{money(price)}[/cyan]  •  "
        f"cash {money(game['cash'])}"
    )

    max_qty = int(game["cash"] // price)
    if max_qty < 1:
        raise click.ClickException(f"Not enough cash to buy even one share at {money(price)}.")
    qty = click.prompt(
        f"Quantity to buy (max {max_qty:,})",
        type=click.IntRange(1, max_qty),
    )

    total = round(qty * price, 2)
    remaining = round(game["cash"] - total, 2)
    print_order_summary("Buy", symbol, qty, price, total, "Total cost", game["cash"], remaining)
    if not click.confirm("Place this order?", default=True):
        console.print("[yellow]Order cancelled.[/yellow]")
        return

    game["cash"] = remaining
    pos = game["holdings"].get(symbol)
    if pos:
        new_shares = pos["shares"] + qty
        pos["avg_cost"] = round((pos["shares"] * pos["avg_cost"] + total) / new_shares, 4)
        pos["shares"] = new_shares
    else:
        game["holdings"][symbol] = {"shares": qty, "avg_cost": price}
    log_transaction(game, "buy", symbol, qty, price, total)
    storage.save_game(game)
    console.print(f"[green]Bought {qty:,} {symbol} @ {money(price)} for {money(total)}.[/green]")


@cli.command("sell")
@click.argument("symbol", required=False)
def sell(symbol):
    """Sell shares of SYMBOL at the current Yahoo Finance price (alias: s).

    If SYMBOL is omitted you'll be prompted for it.
    """
    game = require_game()
    symbol = resolve_symbol(symbol)
    pos = game["holdings"].get(symbol)
    if not pos:
        raise click.ClickException(f"You don't hold any {symbol} in '{game['name']}'.")

    price = fetch_market_price(symbol)
    console.print(
        f"\n[bold]SELL {symbol}[/bold]  •  current price [cyan]{money(price)}[/cyan]  •  "
        f"you hold {pos['shares']:,} @ avg {money(pos['avg_cost'])}"
    )
    qty = click.prompt(
        f"Quantity to sell (max {pos['shares']:,})",
        type=click.IntRange(1, pos["shares"]),
    )

    total = round(qty * price, 2)
    realized = round(qty * (price - pos["avg_cost"]), 2)
    new_cash = round(game["cash"] + total, 2)
    print_order_summary("Sell", symbol, qty, price, total, "Total proceeds", game["cash"], new_cash)
    console.print(f"Realized P/L on this sale: {colored_money(realized)}")
    if not click.confirm("Place this order?", default=True):
        console.print("[yellow]Order cancelled.[/yellow]")
        return

    game["cash"] = new_cash
    pos["shares"] -= qty
    if pos["shares"] == 0:
        del game["holdings"][symbol]
    log_transaction(game, "sell", symbol, qty, price, total, realized_pl=realized)
    storage.save_game(game)
    console.print(f"[green]Sold {qty:,} {symbol} @ {money(price)} for {money(total)}.[/green]")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
