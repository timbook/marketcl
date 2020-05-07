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


class Portfolio:
    def __init__(self, mcl_path):

        config = os.path.join(mcl_path, "config.json")
        with open(config, 'r') as f:
            name = json.load(f)["current"]
            self.game_file = os.path.join(mcl_path, f"game-{name}.json")

        with open(self.game_file, 'r') as f:
            self.data = json.load(f)        

        self.create_df()

    def buy(self):
        sym = input("Enter a ticker to buy: ").lower()
        price = get_one_price(sym)
        cash = self.data["cash"]
        can_buy = int(cash // price)

        print("{} costs ${:,.2f} per share.".format(sym.upper(), price))
        print("You currently have ${:,.2f}".format(cash))
        print("You can buy up to {} shares.".format(can_buy))

        n_buy = int(input("How many would you like to buy? "))
        if n_buy > can_buy:
            print("Insufficient funds! Exiting...")
            sys.exit(1)

        print("You're about to buy {} shares of {} for ${:,.2f} each.".format(
            n_buy, sym.upper(), price
        ))
        print("You'll have ${:,.2f} remaining.".format(cash - n_buy*price))

        ans = input("Are you sure? (Y/n) ")
        if ans == "Y":
            self.add_holding(sym, n_buy, price)
            self.write()
        else:
            print("Close call! Exiting...")
            sys.exit(0)

    def add_holding(self, sym, n_buy, price):
        holding = Holding(sym, n_buy, price)
        self.data["cash"] -= n_buy*price
        self.data["cash"] -= self.data["trade_fee"]
        self.data["total_fee"] += self.data["trade_fee"]
        self.data["portfolio"].append(holding.to_dict())

    def sell(self):
        # List holdings
        self.print()

        # Prompt for ID
        sell_id = int(input("Which holding would you like to sell? "))
        row = self.df.loc[sell_id, :]

        # Prompt for asset
        print()
        print("You have {} shares of {}".format(row.n, row.sym))
        n_sell = int(input("How many would you like to sell? "))

        # Check if possible
        if n_sell > row.n:
            print("You don't have enough shares to sell! Exiting...\n")
            sys.exit(1)

        # Buffer user
        print()
        print("You're about to sell {} shares of {}.".format(n_sell, row.sym))
        ans = input("Are you sure? (Y/n) ")

        # Sell holding and write
        if ans == "Y":
            self.rm_holding(sell_id, n_sell)
            self.write()
        else:
            print("Close call! Exiting...")
            sys.exit(0)

        self.print()

    def rm_holding(self, ix, n_sell):
        # Row to sell
        row = self.df.loc[ix, :]

        n_remaining = self.data["portfolio"][ix]["n"] - n_sell
        if n_remaining == 0:
            self.data["portfolio"].pop(ix)
        else:
            self.data["portfolio"][ix]["n"] -= n_sell

        # Compute cash liquidated, taxes, and capital gains paid, adjust
        # cash holdings in portfolio
        cash_freed = row.price*n_sell
        cap_gain = n_sell*(row.price - row.bought_at)
        cap_gain_paid = cap_gain*self.data["cap_gains_tax"]

        self.data["cash"] += cash_freed
        self.data["cash"] -= cap_gain_paid
        self.data["cash"] -= self.data["trade_fee"]

        self.data["total_tax"] += cap_gain_paid
        self.data["total_fee"] += self.data["trade_fee"]

        # Recreate dataframe with sold asset removed
        self.create_df()

    def create_df(self):
        self.df = pd.DataFrame(self.data["portfolio"])
        self.df.index.name = "ID"

    def print(self):
        syms_full = ' '.join(self.df.sym.unique())
        prices = get_many_prices(syms_full)
        self.df["price"] = self.df.sym.map(prices)
        self.df["total_holding"] = self.df.n*self.df.price
        self.df["pct_profit"] = round((self.df.price - self.df.bought_at) / self.df.bought_at, 3)
        self.df["net_profit"] = self.df.n*(self.df.price - self.df.bought_at)
        print(self.df)

        total_assets = self.data["cash"] + self.df.total_holding.sum()
        total_profit = total_assets - self.data["init_cash"]
        print()
        print("CASH REMAINING: ${:,.2f}".format(self.data["cash"]))
        print("TOTAL FEES PAID: ${:,.2f}".format(self.data["total_fee"]))
        print("TOTAL TAX PAID: ${:,.2f}".format(self.data["total_tax"]))

        print("TOTAL ASSETS: ${:,.2f}".format(total_assets))
        print("TOTAL PROFIT: ${:,.2f}".format(total_profit))
        print()

    def write(self):
        with open(self.game_file, 'w') as f:
            json.dump(self.data, f)

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
