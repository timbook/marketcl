import os
import sys
import json

import pandas as pd
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
    df = yf.download(
        tickers=syms,
        period="5d",
        interval="1m",
        progress=False
    )

    return {sym.upper() : df.Close[sym.upper()].dropna()[-1] for sym in syms.split()}

class Game:
    def __init__(self, mcl_path):

        config = os.path.join(mcl_path, "config.json")
        with open(config, 'r') as f:
            name = json.load(f)["current"]
            self.game_file = os.path.join(mcl_path, f"game-{name}.json")

        with open(self.game_file, 'r') as f:
            game_data_json = json.load(f)
            self.data = GameData(game_data_json)

        self.portfolio = Portfolio(game_data_json["portfolio"])
        self.create_df()

    def buy(self):
        sym = input("Enter a ticker to buy: ").lower()
        price = get_one_price(sym)
        can_buy = int(self.data.cash // price)

        print("{} costs ${:,.2f} per share.".format(sym.upper(), price))
        print("You currently have ${:,.2f}".format(self.data.cash))
        print("You can buy up to {} shares.".format(can_buy))

        n_buy = int(input("How many would you like to buy? "))
        if n_buy > can_buy:
            print("Insufficient funds! Exiting...")
            sys.exit(1)

        print("You're about to buy {} shares of {} for ${:,.2f} each.".format(
            n_buy, sym.upper(), price
        ))
        print("You'll have ${:,.2f} remaining.".format(self.data.cash - n_buy*price))

        ans = input("Are you sure? (Y/n) ")
        if ans == "Y":
            self.add_holding(sym, n_buy, price)
            self.write()
        else:
            print("Close call! Exiting...")
            sys.exit(0)

    def add_holding(self, sym, n_buy, price):
        # New item to buy
        new_holding = Holding(sym, n_buy, price)

        # Adjust cash holdings and total fees paid

        self.data.rm_cash(n_buy*price)
        self.data.pay_fee()

        # Add to portfolio
        self.portfolio.append(new_holding)

    def sell(self):
        # List holdings
        self.print()

        # Prompt for ID
        sell_id = int(input("Which holding would you like to sell? "))
        row = self.df.loc[sell_id, :]

        # Prompt for asset
        print("\nYou have {} shares of {}".format(row.n, row.sym))
        n_sell = int(input("How many would you like to sell? "))

        # Check if possible
        if n_sell > row.n:
            print("You don't have enough shares to sell! Exiting...\n")
            sys.exit(1)

        # Buffer user
        print("\nYou're about to sell {} shares of {}.".format(n_sell, row.sym))
        ans = input("Are you sure? (Y/n) ")

        # Sell holding and write
        if ans == "Y":
            self.rm_holding(sell_id, n_sell)
            self.write()
        else:
            print("Close call! Exiting...")
            sys.exit(0)

    def rm_holding(self, ix, n_sell):
        # Row to sell
        row = self.df.loc[ix, :]

        # Ensure user doesn't sell more than they own
        n_remaining = row.n - n_sell
        if n_remaining == 0:
            self.portfolio.pop(ix)
        else:
            self.portfolio[ix].sell(n_sell)

        # Compute cash liquidated, taxes, and capital gains paid, adjust
        # cash holdings in portfolio
        cash_freed = row.price*n_sell
        cap_gain = n_sell*(row.price - row.bought_at)
        cap_gain_paid = cap_gain*self.data.cap_gains_tax

        self.data.add_cash(cash_freed)
        self.data.pay_tax(n_sell*(row.price - row.bought_at))
        self.data.pay_fee()

    def create_df(self):
        self.df = pd.DataFrame(self.portfolio.to_json())
        self.df.index.name = "ID"

    def print(self):
        syms_full = ' '.join(self.df.sym.unique())
        prices = get_many_prices(syms_full)
        self.df["price"] = self.df.sym.map(prices)
        self.df["total_holding"] = self.df.n*self.df.price
        self.df["pct_profit"] = round((self.df.price - self.df.bought_at) / self.df.bought_at, 3)
        self.df["net_profit"] = self.df.n*(self.df.price - self.df.bought_at)

        # TODO
        self.portfolio.print_table(prices)

        total_assets = self.data.cash + self.df.total_holding.sum()
        total_profit = total_assets - self.data.init_cash

        print()
        print("CASH REMAINING: ${:,.2f}".format(self.data.cash))
        print("TOTAL FEES PAID: ${:,.2f}".format(self.data.total_fee))
        print("TOTAL TAX PAID: ${:,.2f}".format(self.data.total_tax))

        print("TOTAL ASSETS: ${:,.2f}".format(total_assets))
        print("TOTAL PROFIT: ${:,.2f}".format(total_profit))
        print()

    def write(self):
        data_dump = {
            **self.data.to_dict(), 
            "portfolio": self.portfolio.to_json()
        }

        with open(self.game_file, 'w') as f:
            json.dump(data_dump, f)

class GameData:
    def __init__(self, raw_data):
        self.init_cash = raw_data["init_cash"]
        self.cash = raw_data["cash"]
        self.cap_gains_tax = raw_data["cap_gains_tax"]
        self.trade_fee = raw_data["trade_fee"]
        self.total_tax = raw_data["total_tax"]
        self.total_fee = raw_data["total_fee"]

    def rm_cash(self, amount):
        self.cash -= amount

    def add_cash(self, amount):
        self.cash += amount

    def pay_fee(self):
        self.cash -= self.trade_fee
        self.total_fee += self.trade_fee

    def pay_tax(self, amount):
        tax_amount = self.cap_gains_tax * amount
        self.cash -= tax_amount
        self.total_tax += tax_amount

    def to_dict(self):
        return {
            "init_cash": self.init_cash,
            "cash": self.cash,
            "cap_gains_tax": self.cap_gains_tax,
            "trade_fee": self.trade_fee,
            "total_tax": self.total_tax,
            "total_fee": self.total_fee
        }

class Portfolio:
    def __init__(self, raw_data):
        self.items = [Holding(**holding) for holding in raw_data]

    def __getitem__(self, i):
        return self.items[i]

    def pop(self, ix):
        self.items.pop(ix)

    def append(self, holding):
        self.items.append(holding)

    def print_table(self, price_map):
        # Headers
        print(''.join([
            "ID".rjust(3, ' '),
            "Symbol".rjust(8, ' '),
            "N".rjust(6, ' '),
            "Bought At".rjust(12, ' '),
            "Price".rjust(12, ' '),
            "Tot. Value".rjust(14, ' '),
            "% Profit".rjust(10, ' '),
            "Net Profit".rjust(12, ' ')
        ]))
        print("="*80)

        for ix, holding in enumerate(self.items):
            price = price_map[holding.sym]

            print(''.join([
                # ID column
                str(ix).rjust(3, ' '),

                # Symbol column
                holding.sym.upper().rjust(8, ' '),

                # Stock counts
                str(holding.n).rjust(6, ' '),

                # Bought at
                "${:,.2f}".format(holding.bought_at).rjust(12, ' '),

                # Current price
                "${:,.2f}".format(price).rjust(12, ' '),

                # Total value
                "${:,.2f}".format(holding.n * price).rjust(14, ' '),

                # Percentage profit
                "{:,.3f}%".format((price - holding.bought_at)*holding.n/holding.bought_at).rjust(10, ' '),

                # Net profit
                "${:,.2f}".format((price - holding.bought_at)*holding.n).rjust(12, ' '),
            ]))


    def to_json(self):
        return [item.to_dict() for item in self.items]

class Holding:
    def __init__(self, sym, n, bought_at):
        self.sym = sym.upper()
        self.n = n
        self.bought_at = bought_at

    def to_dict(self):
        return {
            "sym": self.sym,
            "n": self.n,
            "bought_at": self.bought_at
        }

    def sell(self, n):
        self.n -= n
