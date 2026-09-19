"""Pure, broker-independent primitives. Percentages are fractions, e.g. .005."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
from math import isfinite


def finite(*values):
    if not all(isfinite(x) for x in values):
        raise ValueError("non-finite input")


@dataclass(frozen=True)
class Setup:
    symbol: str
    side: str
    entry: float
    stop: float
    timestamp: int

    def __post_init__(self):
        finite(self.entry, self.stop)
        if self.side not in ("buy", "sell") or min(self.entry, self.stop) <= 0:
            raise ValueError("invalid setup")
        if (self.entry - self.stop) * self.direction <= 0:
            raise ValueError("stop must be on the loss side")

    @property
    def direction(self):
        return 1 if self.side == "buy" else -1

    @property
    def risk_distance(self):
        return abs(self.entry - self.stop)

    @property
    def targets(self):
        return tuple(self.entry + self.direction * self.risk_distance * n for n in (1, 2, 3))


@dataclass(frozen=True)
class RiskSnapshot:
    equity: float
    floating_reference: float
    daily_floor: float
    total_floor: float
    existing_stop_risk: float  # Additional loss FROM CURRENT equity, including pending orders.
    recorded_at: int
    rules_verified: bool = False


def risk_budget(s: RiskSnapshot, *, now: int, floating_limit: float,
                trade_fraction: float, buffer_fraction: float = .002,
                max_age: int = 10) -> float:
    """Returns account-currency budget; caller must supply verified monetary floors.

    Does not invent a daily reset timezone, trailing rule or equity reference.
    All positions, including manual ones, must be included in existing_stop_risk.
    """
    finite(s.equity, s.floating_reference, s.daily_floor, s.total_floor,
           s.existing_stop_risk, floating_limit, trade_fraction, buffer_fraction)
    if not s.rules_verified or not 0 <= now - s.recorded_at <= max_age:
        return 0.
    if min(s.equity, s.floating_reference) <= 0 or s.existing_stop_risk < 0:
        return 0.
    if not 0 < floating_limit < 1 or not 0 < trade_fraction < 1 or not 0 <= buffer_fraction < 1:
        raise ValueError("invalid risk fraction")
    floor = max(s.daily_floor, s.total_floor, s.floating_reference * (1-floating_limit))
    available = s.equity - floor - s.existing_stop_risk - s.floating_reference * buffer_fraction
    return max(0., min(s.equity * trade_fraction, available))


def lot_size(budget, loss_per_lot, costs_per_lot, step, minimum, maximum):
    """loss_per_lot must come from broker's profit calculator in account currency."""
    finite(budget, loss_per_lot, costs_per_lot, step, minimum, maximum)
    if budget <= 0 or loss_per_lot <= 0 or costs_per_lot < 0 or step <= 0 or minimum <= 0 or maximum < minimum:
        return 0.
    d = lambda x: Decimal(str(x))
    quantity = min(d(maximum), d(budget) / (d(loss_per_lot) + d(costs_per_lot)))
    quantity = (quantity / d(step)).to_integral_value(rounding=ROUND_FLOOR) * d(step)
    return float(quantity) if quantity >= d(minimum) else 0.


def split_volume(volume, step, minimum):
    finite(volume, step, minimum)
    if min(volume, step, minimum) <= 0:
        raise ValueError("invalid volume")
    v, st, mn = map(lambda x: Decimal(str(x)), (volume, step, minimum))
    if v % st:
        raise ValueError("volume does not match step")
    first = (v / st / 3).to_integral_value(rounding=ROUND_FLOOR) * st
    parts = (first, first, v - 2 * first)
    if min(parts) < mn:
        raise ValueError("volume too small for three exits")
    return tuple(float(x) for x in parts)


@dataclass
class PaperPosition:
    """Quote-based simulator, NOT a broker executor. Close uses executable bid/ask."""
    setup: Setup
    volume: float = .03
    step: float = .01
    minimum: float = .01
    next_target: int = 0
    closed: bool = False
    pnl_r: float = 0.

    def __post_init__(self):
        self.parts = split_volume(self.volume, self.step, self.minimum)
        self.stop = self.setup.stop
        self.remaining = self.volume

    def quote(self, bid, ask):
        finite(bid, ask)
        if bid <= 0 or ask < bid:
            raise ValueError("invalid quote")
        if self.closed:
            return []
        price = bid if self.setup.side == "buy" else ask
        direction = self.setup.direction
        if (price - self.stop) * direction <= 0:
            self.pnl_r += ((price-self.setup.entry) * direction / self.setup.risk_distance) * (self.remaining/self.volume)
            self.remaining = 0.
            self.closed = True
            return ["SL"]
        events = []
        while self.next_target < 3 and (price-self.setup.targets[self.next_target]) * direction >= 0:
            i = self.next_target
            # Conservative limit fill at target, not a favorable gap price.
            self.pnl_r += (i+1) * self.parts[i] / self.volume
            self.remaining -= self.parts[i]
            self.next_target += 1
            events.append(f"TP{i+1}")
            if i == 0:
                self.stop = self.setup.entry
                events.append("BREAKEVEN")
        if self.next_target == 3:
            self.closed = True
            self.remaining = 0.
        return events
