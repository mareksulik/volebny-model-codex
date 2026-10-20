import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import unittest,json,tempfile
from evaluate import score_race,evaluate
from verify_lock import verify
from freeze import freeze
from datetime import datetime
from zoneinfo import ZoneInfo

class EvaluationRequirements(unittest.TestCase):
    def setUp(self):
        self.race=dict(id='x',name='X',category='city',polls_used=[],candidates=[dict(id='a',active=True,estimate_pct=60,low80_pct=45,high80_pct=75,win_probability=.8),dict(id='b',active=True,estimate_pct=40,low80_pct=25,high80_pct=55,win_probability=.2)])
        self.actual=dict(race_id='x',votes={'a':60,'b':40},source_url='https://volby.statistics.sk/test')
    def test_perfect_share_and_probabilistic_score(self):
        score=score_race(self.race,self.actual)
        self.assertEqual(score['absolute_error_sum'],0);self.assertAlmostEqual(score['brier'],.08)
        self.assertEqual(score['covered_count'],2);self.assertEqual(score['winner_hit'],1)
    def test_actual_tie_is_unresolved(self):
        score=score_race(self.race,{**self.actual,'votes':{'a':50,'b':50}})
        self.assertTrue(score['tied']);self.assertIsNone(score['brier']);self.assertIsNone(score['winner_hit'])
    def test_invalid_actuals_and_missing_coverage(self):
        for votes in [{'a':100},{'a':-1,'b':2},{'a':0,'b':0},{'a':True,'b':1},{'a':.5,'b':1}]:
            with self.subTest(votes=votes),self.assertRaises(ValueError):score_race(self.race,{**self.actual,'votes':votes})
        with self.assertRaises(ValueError):score_race(self.race,{**self.actual,'source_url':'https://example.com'})
        with self.assertRaises(ValueError):evaluate({'races':[self.race],'cutoff':'x'},{'races':[]})
    def test_lock_detects_mutation_and_permission_error(self):
        import hashlib
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir();(root/'a.txt').write_text('original')
            (root/'data/LOCK.json').write_text(json.dumps({'files':{'a.txt':hashlib.sha256(b'original').hexdigest()}}))
            verify(root)
            with patch.object(Path,'read_bytes',side_effect=PermissionError('denied')):
                with self.assertRaises(PermissionError):verify(root)
            (root/'a.txt').write_text('mutated')
            with self.assertRaises(ValueError):verify(root)
            (root/'a.txt').unlink()
            with self.assertRaises(ValueError):verify(root)
    def test_cannot_freeze_twice_or_after_deadline(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir();(root/'data/LOCK.json').write_text('{}')
            with self.assertRaises(ValueError):freeze(root)
            (root/'data/LOCK.json').unlink()
            with self.assertRaises(ValueError):freeze(root,datetime(2026,10,22,tzinfo=ZoneInfo('Europe/Bratislava')))

if __name__=='__main__':unittest.main()
