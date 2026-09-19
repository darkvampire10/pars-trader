"""Closed-candle breakout/retest candidate detector. No profitability claim."""
from dataclasses import dataclass
from .core import Setup, finite


@dataclass(frozen=True)
class Bar:
    time: int  # UTC OPEN time, Unix seconds
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self):
        finite(self.open, self.high, self.low, self.close)
        if self.time < 0 or self.low <= 0 or self.high < max(self.open, self.close, self.low) or self.low > min(self.open, self.close):
            raise ValueError("invalid candle")


def closed_bars(bars, seconds, now):
    if any(a.time >= b.time for a, b in zip(bars, bars[1:])):
        raise ValueError("bars must be strictly chronological")
    return [b for b in bars if b.time + seconds <= now]


def pivots(bars, highs=True):
    values = [b.high if highs else b.low for b in bars]
    result = []
    for i in range(2, len(bars)-2):
        peers = values[i-2:i] + values[i+1:i+3]
        if all(values[i] > x if highs else values[i] < x for x in peers):
            result.append((i, values[i]))
    return result


def atr(bars, period=14):
    if len(bars) < period+1:
        raise ValueError("insufficient ATR history")
    ranges = [max(b.high-b.low, abs(b.high-a.close), abs(b.low-a.close)) for a,b in zip(bars,bars[1:])]
    return sum(ranges[-period:])/period


def detect(symbol, m1, m5, m15, bid, ask, now):
    finite(bid, ask)
    if bid <= 0 or ask < bid:
        return None
    m1, m5, m15 = (closed_bars(bars, seconds, now) for bars,seconds in ((m1,60),(m5,300),(m15,900)))
    if len(m1)<3 or len(m5)<25 or len(m15)<25:
        return None
    if any(now-bars[-1].time-seconds > 90 for bars,seconds in ((m1,60),(m5,300),(m15,900))):
        return None
    highs, lows = pivots(m15), pivots(m15, False)
    if len(highs)<2 or len(lows)<2:
        return None
    up = highs[-1][1]>highs[-2][1] and lows[-1][1]>lows[-2][1]
    down = highs[-1][1]<highs[-2][1] and lows[-1][1]<lows[-2][1]
    if not (up or down):
        return None
    direction = 1 if up else -1
    # Search at most six CLOSED retest candles after a breakout.
    for j in range(len(m5)-2, max(16, len(m5)-8)-1, -1):
        history = m5[:j]
        levels = pivots(history, highs=up)
        if not levels:
            continue
        level = levels[-1][1]
        breakout = m5[j]
        if (breakout.close-level)*direction <= 0 or (m5[j-1].close-level)*direction > 0:
            continue
        volatility = atr(history)
        if volatility <= 0:
            continue
        after = m5[j+1:]
        tolerance = .15*volatility
        touches = [b for b in after if b.low <= level+tolerance and b.high >= level-tolerance]
        if not touches:
            continue
        if any((b.close-level)*direction < -tolerance for b in after):
            continue
        confirmation, previous = m1[-1], m1[-2]
        if confirmation.time < touches[0].time+300:
            continue
        if not (confirmation.close>previous.high if up else confirmation.close<previous.low):
            continue
        entry = ask if up else bid
        # Include all known M1 extremes since the first retest, including the trigger.
        recent = [b for b in m1 if b.time >= touches[0].time]
        extremes = after + recent
        stop = min(b.low for b in extremes)-.2*volatility if up else max(b.high for b in extremes)+.2*volatility
        if (entry-stop)*direction <= 0:
            continue
        setup = Setup(symbol, "buy" if up else "sell", entry, stop, breakout.time)
        if ask-bid <= .1*setup.risk_distance:
            return setup
    return None
