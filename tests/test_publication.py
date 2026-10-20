import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import unittest,json,csv
from html.parser import HTMLParser
from prepare import ROOT,DATA
from model import blend_polls
from build import apply_events,create_forecast
from datetime import date

class PublicationRequirements(unittest.TestCase):
    def test_every_included_poll_uses_registered_candidate_field(self):
        races=apply_events(json.loads((DATA/'races-register.json').read_text()),json.loads((DATA/'events.json').read_text()))
        polls=json.loads((DATA/'polls.json').read_text())
        for race in races:
            active=[c for c in race['candidates'] if c['active']]
            prior=[1/len(active)]*len(active)
            result=blend_polls(prior,active,[p for p in polls if p['race_id']==race['id']],date(2026,10,20),[c['name'] for c in race['candidates'] if not c['active']])
            self.assertAlmostEqual(sum(result[0]),1)
    def test_source_urls_are_public_https(self):
        sources=json.loads((DATA/'sources.json').read_text())
        self.assertGreater(len(sources),20)
        self.assertTrue(all(s.get('url','').startswith('https://') for s in sources))
    def test_csv_matches_snapshot(self):
        with (ROOT/'docs/data/forecast.csv').open() as file:
            rows=list(csv.DictReader(file))
        forecast=json.loads((ROOT/'docs/data/forecast.json').read_text())
        candidates={c['id']:c for r in forecast['races'] for c in r['candidates']}
        self.assertEqual(len(rows),len(candidates))
        for row in rows:
            self.assertAlmostEqual(float(row['estimate_pct']),candidates[row['candidate_id']]['estimate_pct'])
    def test_static_tables_cover_all_races(self):
        text=(ROOT/'docs/all.html').read_text()
        self.assertEqual(text.count('class="all-race"'),33)
        for r in json.loads((ROOT/'docs/data/forecast.json').read_text())['races']:
            self.assertIn('id="'+r['id']+'"',text)
    def test_browser_exports_and_styles_exist(self):
        for name in ['index.html','app.js','style.css','METHODOLOGY.md','all.html','data/odds.json','data/polls.json','data/sources.json','data/fit.json','data/evaluation.json']:
            self.assertTrue((ROOT/'docs'/name).is_file(),name)

if __name__=='__main__':unittest.main()
