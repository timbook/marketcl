import os
import sys
import json

import yfinance as yf
import pandas as pd

from .items import Portfolio, Holding
from .utils import get_one_price, get_many_prices, color_picker

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
        if row.price > row.bought_at:
            self.data.pay_tax(n_sell*(row.price - row.bought_at))
        self.data.pay_fee()

    def create_df(self):
        self.df = pd.DataFrame(self.portfolio.to_json())
        self.df.index.name = "ID"

    def print(self):
        if self.df.shape[0] > 0:
            syms_full = ' '.join(self.df.sym.unique())
            prices = get_many_prices(syms_full)
            self.df["price"] = self.df.sym.map(prices)
            self.df["total_holding"] = self.df.n*self.df.price
            self.df["pct_profit"] = round((self.df.price - self.df.bought_at) / self.df.bought_at, 3)
            self.df["net_profit"] = self.df.n*(self.df.price - self.df.bought_at)
            self.portfolio.print_table(prices)
            total_holdings = self.df.total_holding.sum()
        else:
            print()
            print("[ Your portfolio is currently empty. Buy some stock to get started! ]")
            total_holdings = 0

        total_assets = self.data.cash + total_holdings
        total_profit = total_assets - self.data.init_cash
        pct_profit = 100*total_profit / self.data.init_cash

        color = color_picker("green" if total_profit >= 0 else "red")

        print()
        print("CASH REMAINING:  ${:>10,.2f}".format(self.data.cash))
        print("TOTAL FEES PAID: ${:>10,.2f}".format(self.data.total_fee))
        print("TOTAL TAX PAID:  ${:>10,.2f}".format(self.data.total_tax))

        print()
        print("TOTAL ASSETS:".ljust(17, ' ') + color("${:>10,.2f}".format(total_assets)))
        print("TOTAL PROFIT:".ljust(17, ' ') + color("${:>10,.2f}".format(total_profit)))
        print("PERCENT PROFIT:".ljust(17, ' ') + color(" {:>10,.2f}%".format(pct_profit)))
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
