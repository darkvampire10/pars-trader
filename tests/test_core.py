import unittest
from dataclasses import replace
from pars_trader.core import Setup, PaperPosition, RiskSnapshot, risk_budget, lot_size, split_volume


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = RiskSnapshot(10000,10000,9600,9200,0,100,True)

    def budget(self,s=None,**kwargs):
        return risk_budget(s or self.snapshot,now=100,floating_limit=.03,trade_fraction=.005,**kwargs)

    def test_per_trade_cap(self):
        self.assertEqual(self.budget(),50)

    def test_shared_floating_budget(self):
        self.assertEqual(self.budget(replace(self.snapshot,existing_stop_risk=270)),10)

    def test_daily_floor_can_bind(self):
        self.assertEqual(self.budget(replace(self.snapshot,daily_floor=9990)),0)

    def test_unverified_rules_fail_closed(self):
        self.assertEqual(self.budget(replace(self.snapshot,rules_verified=False)),0)

    def test_stale_and_future_data_fail_closed(self):
        for timestamp in (0,101):
            self.assertEqual(self.budget(replace(self.snapshot,recorded_at=timestamp)),0)

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            self.budget(replace(self.snapshot,equity=float('nan')))

    def test_lots_round_down_and_include_costs(self):
        self.assertEqual(lot_size(100,300,20,.01,.01,100),.31)
        self.assertEqual(lot_size(1,300,20,.01,.01,100),0)

    def test_volume_split_conserves_volume(self):
        self.assertEqual(split_volume(.1,.01,.01),(.03,.03,.04))

    def test_small_or_unaligned_volume_rejected(self):
        for value in (.02,.035):
            with self.assertRaises(ValueError):
                split_volume(value,.01,.01)


class ExitTests(unittest.TestCase):
    def test_three_targets_pay_two_r(self):
        p = PaperPosition(Setup('TEST','buy',100,99,0))
        self.assertEqual(p.quote(103,103.1),['TP1','BREAKEVEN','TP2','TP3'])
        self.assertAlmostEqual(p.pnl_r,2)
        self.assertTrue(p.closed)

    def test_partial_then_breakeven(self):
        p = PaperPosition(Setup('TEST','buy',100,99,0))
        p.quote(101,101.1)
        self.assertEqual(p.stop,100)
        self.assertEqual(p.quote(100,100.1),['SL'])
        self.assertAlmostEqual(p.pnl_r,1/3)

    def test_short_exits_use_ask(self):
        p = PaperPosition(Setup('TEST','sell',100,101,0))
        self.assertEqual(p.quote(98.9,99.1),[])
        self.assertEqual(p.quote(98.9,99),['TP1','BREAKEVEN'])

    def test_gap_stop_fills_at_quote(self):
        p = PaperPosition(Setup('TEST','buy',100,99,0))
        p.quote(98,98.1)
        self.assertAlmostEqual(p.pnl_r,-2)

    def test_repeated_quotes_do_not_repeat_exits(self):
        p = PaperPosition(Setup('TEST','buy',100,99,0))
        p.quote(101,101.1)
        self.assertEqual(p.quote(101,101.1),[])

    def test_invalid_direction_rejected(self):
        with self.assertRaises(ValueError):
            Setup('TEST','buy',100,101,0)
