import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import unittest,json
from collections import Counter,defaultdict
from prepare import ROOT,DATA,key
from build import apply_events

class DataRequirements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.races=json.loads((DATA/'races-register.json').read_text());cls.history=json.loads((DATA/'history.json').read_text())
    def test_exact_scope_and_ids(self):
        self.assertEqual(Counter(r['category'] for r in self.races),{'region':8,'city':8,'borough':17})
        ids=[c['id'] for r in self.races for c in r['candidates']]
        self.assertEqual(len(ids),148);self.assertEqual(len(ids),len(set(ids)))
    def test_distinct_kosice_names(self):
        race=next(r for r in self.races if r['id']=='city-kosice')
        self.assertEqual(len([c for c in race['candidates'] if 'Lörinc' in c['name']]),2)
    def test_all_historic_shares_match_official(self):
        for r in self.history:
            with self.subTest(row=(r['year'],r['code'],r['name'])):
                self.assertAlmostEqual(r['reported_pct'],r['share']*100,delta=.02)
    def test_historic_ballot_identity(self):
        ids=[(r['year'],r['office'],r['code'],r['ballot']) for r in self.history]
        self.assertEqual(len(ids),len(set(ids)))
        topolnica=[r for r in self.history if r['year']==2018 and r['code']=='504084']
        self.assertEqual(sum(r['votes'] for r in topolnica),395)
    def test_withdrawals_preserve_registry(self):
        events=json.loads((DATA/'events.json').read_text())
        result=apply_events(self.races,events)
        self.assertEqual(sum(not c['active'] for r in result for c in r['candidates']),9)
        self.assertEqual(sum(len(r['candidates']) for r in result),148)
        self.assertTrue(all(c['active'] for r in self.races for c in r['candidates']))
    def test_training_partition_no_leakage(self):
        fit=json.loads((DATA/'fit.json').read_text())
        a,b,c=[set(fit[name+'_ids']) for name in ['train','calibration','test']]
        self.assertFalse(a&b or b&c or a&c)
        self.assertEqual(len(c),fit['test']['races'])
    def test_public_data_complete(self):
        forecast=json.loads((ROOT/'docs/data/forecast.json').read_text())
        self.assertEqual({r['id'] for r in self.races},{r['id'] for r in forecast['races']})
        for r in forecast['races']:
            self.assertAlmostEqual(sum(c['estimate_pct'] for c in r['candidates']),100)
            self.assertAlmostEqual(sum(c['win_probability'] for c in r['candidates']),1)
            for c in r['candidates']:
                self.assertTrue(0<=c['win_probability']<=1)
                self.assertTrue(0<=c['low80_pct']<=c['high80_pct']<=100)
                if not c['active']:self.assertEqual(c['estimate_pct'],0)

if __name__=='__main__':unittest.main()
