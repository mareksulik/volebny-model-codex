import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import unittest
from datetime import date
from model import normalize,simulate,blend_polls,features,market_probabilities

class ModelRequirements(unittest.TestCase):
    def test_percentages_and_plurality(self):
        result=simulate([.4,.35,.25],30,4000,9)
        self.assertAlmostEqual(sum(c['estimate_pct'] for c in result),100)
        self.assertAlmostEqual(sum(c['win_probability'] for c in result),1)
        self.assertGreater(result[0]['win_probability'],result[1]['win_probability'])
        self.assertGreater(result[0]['win_probability'],.4)
    def test_single_candidate(self):
        self.assertEqual(simulate([1],6,100)[0],dict(estimate_pct=100,low80_pct=100,high80_pct=100,win_probability=1))
    def test_reproducible_and_boundaries(self):
        a=simulate([.0001,.4999,.5],6,1000,77)
        self.assertEqual(a,simulate([.0001,.4999,.5],6,1000,77))
        for c in a:self.assertTrue(0<=c['low80_pct']<=c['high80_pct']<=100)
    def test_invalid_inputs(self):
        for values in [[],[0,0],[-1,2],[float('nan'),1],[float('inf'),1]]:
            with self.subTest(values=values),self.assertRaises(ValueError):normalize(values)
        for concentration in [0,-1,float('inf')]:
            with self.subTest(concentration=concentration),self.assertRaises(ValueError):simulate([.5,.5],concentration,100)
    def test_symmetric_contest_and_zero_support(self):
        result=simulate([.5,.5,0],30,10000,8)
        self.assertAlmostEqual(result[0]['win_probability'],.5,delta=.03)
        self.assertEqual(result[2]['high80_pct'],0)
    def test_homonymous_history_is_not_silently_matched(self):
        candidate={'name':'Ján Novák','job':'','party':'NK/NEKA'}
        self.assertEqual(features(candidate,[{'name':'Ján Novák','share':.8,'winner':True},{'name':'Ján Novák','share':.2}])[:2],[0,0])
    def test_polls_future_and_field_validation(self):
        candidates=[{'name':'A'},{'name':'B'}]
        poll=dict(id='p',published='2026-10-01',fieldwork_end='2026-09-30',n_local=100,included=True,shares={'A':60,'B':40})
        mean,used,mass=blend_polls([.5,.5],candidates,[poll],date(2026,10,20))
        self.assertGreater(mean[0],.5);self.assertTrue(used);self.assertEqual(mass,0)
        with self.assertRaises(ValueError):blend_polls([.5,.5],candidates,[{**poll,'published':'2026-10-22'}],date(2026,10,20))
        with self.assertRaises(ValueError):blend_polls([.5,.5],candidates,[{**poll,'shares':{'A':60}}],date(2026,10,20))
    def test_withdrawal_and_undecided_scenario(self):
        poll=dict(id='p',published='2026-10-01',fieldwork_end=None,n_local=None,included=True,shares={'A':50,'B':30,'X':10},undecided_pct=10)
        mean,used,mass=blend_polls([.5,.5],[{'name':'A'},{'name':'B'}],[poll],date(2026,10,20),['X'])
        self.assertGreater(mass,0);self.assertAlmostEqual(sum(mean),1)
        result=simulate(mean,20,1000,2,mass,[.5,.5])
        self.assertAlmostEqual(sum(c['win_probability'] for c in result),1)
    def test_market_margin(self):
        self.assertEqual(market_probabilities([2,2]),[.5,.5])
        self.assertAlmostEqual(sum(market_probabilities([1.5,3,12])),1)
        with self.assertRaises(ValueError):market_probabilities([1,2])

if __name__=='__main__':unittest.main()
