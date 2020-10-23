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
            "macd": self.plot_macd
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
