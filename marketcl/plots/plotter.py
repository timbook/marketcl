import numpy as np
import matplotlib.pyplot as plt

import yfinance as yf

class Plotter:
    def __init__(self, sym):
        self.sym = sym
        self.data = yf.download(tickers=sym, period='6mo', interval='1d', progress=False)
        self.data.columns = ['open', 'high', 'low', 'close', 'adjclose', 'volume']

    def plot(self, choice):
        plot_dispatch = {
            "macd": self.plot_macd,
            "sroc": self.plot_sroc,
            "wr": self.plot_wr
        }
        plot_dispatch[choice]()

    def plot_price(self, ax):
        ax.set_title("Price", loc="left")
        ax.plot(self.data.index, self.data.close, color="black")

    def plot_volume(self, ax):
        ax.set_title("Volume", loc="left")
        ax.vlines(self.data.index, ymin=0, ymax=self.data.volume, color="black")
        ax.ticklabel_format(axis='y', style='plain')

    def plot_macd(self):
        ema12 = self.data.close.ewm(span=12).mean()
        ema26 = self.data.close.ewm(span=26).mean()
        fast_line = ema12 - ema26
        slow_line = fast_line.ewm(span=9).mean()
        macd_hist = fast_line - slow_line
        color = np.where(macd_hist > 0, "darkgreen", "darkred")
        
        fig, axs = plt.subplots(2, 2, figsize=(14, 8))

        self.plot_price(axs[0][0])
        self.plot_volume(axs[1][0])

        axs[0][1].set_title("MACD", loc="left")
        axs[0][1].plot(self.data.index, fast_line, color="navy", label="Fast Line")
        axs[0][1].plot(self.data.index, slow_line, color="skyblue", ls="dashed", label="Slow Line")

        axs[1][1].set_title("MACD Histogram", loc="left")
        axs[1][1].vlines(self.data.index, ymin=0, ymax=macd_hist, color=color)

        axs[0][1].legend()
        plt.tight_layout()
        plt.show()

    def plot_sroc(self):
        ema = self.data.close.ewm(span=13).mean()
        ema_shift = ema.shift(21)
        roc = ema / ema_shift
        centerline = (roc.max() + roc.min()) / 2
        meanline = roc.mean()

        fig, axs = plt.subplots(3, 1, figsize=(14, 8))

        self.plot_price(axs[0])
        self.plot_volume(axs[1])

        axs[2].set_title("Smoothed Rate of Change", loc="left")
        axs[2].plot(self.data.index, roc, color="navy")
        axs[2].axhline(centerline, color="black")

        plt.tight_layout()
        plt.show()

    def plot_wr(self):
        h7 = self.data.high.rolling(7).max()
        l7 = self.data.low.rolling(7).min()
        wr = (h7 - self.data.close) / (h7 - l7)

        U = wr.max()
        L = wr.min()
        high_ref = U - (U - L)*0.10
        low_ref = L + (U - L)*0.10

        fig, axs = plt.subplots(3, 1, figsize=(14, 8))

        self.plot_price(axs[0])
        self.plot_volume(axs[1])

        axs[2].set_title("Williams %R", loc="left")
        axs[2].plot(self.data.index, wr, color="navy")
        axs[2].axhline(high_ref, color="black")
        axs[2].axhline(low_ref, color="black")

        plt.tight_layout()
        plt.show()
