import json
import math
import tempfile
import unittest
from pathlib import Path
from pars_trader.store import Store
from pars_trader.telegram import handle
from pars_trader.news import news_clear
from pars_trader.strategy import Bar, closed_bars, pivots, detect
from pars_trader.scanner import scan


class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.store = Store(self.path/'state.sqlite3')

    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()

    def message(self,text, sender=123, chat=123, kind='private'):
        return {'from':{'id':sender},'chat':{'id':chat,'type':kind},'text':text}

    def test_owner_only_private_chat(self):
        for message in (self.message('/signals',sender=999),self.message('/signals',kind='group'),self.message('/signals',chat=999)):
            self.assertIsNone(handle(message,123,self.store))
        self.assertTrue(self.store.get('paused',True))

    def test_selection_survives_restart(self):
        handle(self.message('/one'),123,self.store)
        second = Store(self.path/'state.sqlite3')
        self.assertEqual(second.get('plan'),'one')
        second.db.close()

    def test_live_command_never_enables_execution(self):
        handle(self.message('/live'),123,self.store)
        self.assertIsNone(self.store.get('live'))

    def test_no_password_persistence(self):
        handle(self.message('a-secret-password'),123,self.store)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM settings').fetchone()[0],0)

    def test_dedup_survives_restart(self):
        self.assertTrue(self.store.add_signal('one',{'text':'test'},1))
        self.assertFalse(self.store.add_signal('one',{'text':'test'},2))

    def test_invalid_balance(self):
        for value in ('nan','inf','-1'):
            handle(self.message('/balance '+value),123,self.store)
            self.assertIsNone(self.store.get('paper_balance'))

    def test_news_coverage_and_event_blackout(self):
        path = self.path/'calendar.json'
        data = {'generated_at':10000,'coverage_start':0,'coverage_end':20000,'currencies':['XAU','USD'],'events':[]}
        path.write_text(json.dumps(data))
        self.assertTrue(news_clear(path,'XAUUSD',10000))
        data['events'] = [{'time':10900,'currency':'USD','impact':'high'}]
        path.write_text(json.dumps(data))
        self.assertFalse(news_clear(path,'XAUUSD',10000))
        self.assertFalse(news_clear(path,'EURUSD',10000))
        self.assertFalse(news_clear(path,'XAUUSD',20000))

    def test_missing_calendar_blocks(self):
        self.assertFalse(news_clear(self.path/'missing','XAUUSD',100))

    def test_old_snapshot_rejected(self):
        path = self.path/'market.json'
        path.write_text(json.dumps({'generated_at':0,'symbols':{}}))
        with self.assertRaises(ValueError):
            scan(path,self.path/'calendar.json',['XAUUSD'],1000)


class StrategyTests(unittest.TestCase):
    def test_future_bar_never_used(self):
        bars = [Bar(0,100,101,99,100),Bar(60,100,1000,1,500)]
        self.assertEqual(closed_bars(bars,60,90),bars[:1])

    def test_pivot_requires_two_future_closed_bars(self):
        bars = [Bar(i*60,100,high,99,100) for i,high in enumerate([101,102,105,103,102])]
        self.assertEqual(pivots(bars[:4]),[])
        self.assertEqual(pivots(bars),[(2,105)])

    def test_chronology_enforced(self):
        with self.assertRaises(ValueError):
            closed_bars([Bar(60,100,101,99,100),Bar(0,100,101,99,100)],60,1000)

    def test_no_history_no_setup(self):
        self.assertIsNone(detect('TEST',[],[],[],100,101,1000))

    def test_breakout_retest_candidate(self):
        now = 45000
        m15=[]
        for i in range(50):
            v=80+i*.3+math.sin(i*math.pi/3)*2
            m15.append(Bar(i*900,v,v+.4,v-.4,v))
        m5=[]
        for i in range(32):
            v=100+math.sin(i*math.pi/2)
            m5.append(Bar(now-35*300+i*300,v,v+.3,v-.3,v))
        m5 += [Bar(now-900,100.5,102.4,100.4,102),Bar(now-600,102,102.1,101.1,101.4),Bar(now-300,101.4,101.9,101.3,101.7)]
        m1=[Bar(now-180,101.5,101.8,101.4,101.6),Bar(now-120,101.6,101.9,101.5,101.8),Bar(now-60,101.8,102.2,101.7,102)]
        setup=detect('TEST',m1,m5,m15,102,102.01,now)
        self.assertIsNotNone(setup)
        self.assertEqual(setup.side,'buy')
        self.assertLess(setup.stop,setup.entry)
