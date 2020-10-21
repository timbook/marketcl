from .utils import color_picker

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
        print()
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
        print("="*77)

        for ix, holding in enumerate(self.items):
            price = price_map[holding.sym]
            holding.print_row(ix, price)

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

    def print_row(self, ix, price):
        # ID
        id_col = str(ix).rjust(3, ' ')

        # Symbol
        sym_col = self.sym.upper().rjust(8, ' ')

        # N stock
        n_col = str(self.n).rjust(6, ' ')

        # Bought at
        bought_at_col = "${:,.2f}".format(self.bought_at).rjust(12, ' ')

        # Current price
        curr_price_col = "${:,.2f}".format(price).rjust(12, ' ')

        # Total value
        tot_val_col = "${:,.2f}".format(self.n * price).rjust(14, ' ')

        # % Profit
        pct_profit_col = "{:,.3f}%".format(
            100*(price - self.bought_at) / self.bought_at
        ).rjust(10, ' ')

        # $ Profit
        dollar_profit_col = "${:,.2f}".format(
            (price - self.bought_at)*self.n
        ).rjust(12, ' ')

        color = color_picker("green" if price >= self.bought_at else "red")
        print(''.join([
            id_col,
            sym_col,
            n_col,
            bought_at_col,
            curr_price_col,
            tot_val_col,
            color(pct_profit_col),
            color(dollar_profit_col)
        ]))
