MACD_DESC = """
From "Trading for a Living", by Dr. Alexander Elder

MACD TRADING RULES
------------------
1. When the fast MACD line crosses above the slow Signal line, it gives a buy
   signal. Go long, and place a protective stop below the latest minor low.
2. When the fast line crosses below the slow line, it gives a sell signal. Go
   short, and place a protective stop above the latest minor high.

MACD HISTOGRAM TRADING RULES
----------------------------
MACD-Histograms give two types of trading signals. One is common and occurs at
every price bar. The other is rare and occurs only a few times a year in any
market - but is extremely strong.

The common signal is given by the slope of the MACD-Histogram. When the current
bar is higher than the proceeding bar, the slope is up. It shows that bulls are
in control and it is time to buy. When teh current bar is lower than the
preceding bar, the slope is down. It shows that bears are in control and it is
time to be short. When prices go one way but MACD-Histogram moves the other
way, it shows that the dominant crowd is losing its enthusiasm and the trend is
weaker than it appears.

1. Buy when MACD-Histogram stops falling and ticks up. Place a protective stop
   below the latest minor low.
2. Sell short when MACD-Histogram stops rising and ticks down. Place a
   protective stop above the latest minor high.
3. [STRONGEST SIGNAL] Sell short when MACD-Histogram ticks down from its
   second, lower top, while prices are at a new high. Place a protective stop
   above the latest high.
4. [STRONGEST SIGNAL] Buy when MACD-Histogram ticks up from its second more
   shallow bottom while prices are at a new low. Place a protective stop below
   the latest low.
"""

description_dispatch = {
    "macd": MACD_DESC
}

def plot_desc(kind):
    print(description_dispatch[kind])
