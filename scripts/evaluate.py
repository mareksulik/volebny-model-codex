"""Score official vote counts against the original locked candidate forecast."""
import argparse
from collections import defaultdict
from datetime import datetime
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo
from prepare import ROOT,dump
from verify_lock import verify

def score_race(forecast,actual):
    expected={c['id'] for c in forecast['candidates'] if c['active']}
    if set(actual['votes'])!=expected:raise ValueError('Actual candidate set differs: '+forecast['id'])
    votes=actual['votes']
    if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in votes.values()) or sum(votes.values())<=0:
        raise ValueError('Vote counts must be nonnegative integers with positive total')
    if not actual.get('source_url','').startswith(('https://volby.statistics.sk/','https://www.volbysr.sk/','https://volbysr.sk/')):
        raise ValueError('Official results source required')
    winners=[identity for identity,value in votes.items() if value==max(votes.values())]
    candidates=[c for c in forecast['candidates'] if c['active']]
    errors=[c['estimate_pct']-100*votes[c['id']]/sum(votes.values()) for c in candidates]
    covered=[c['low80_pct']<=100*votes[c['id']]/sum(votes.values())<=c['high80_pct'] for c in candidates]
    unique=len(winners)==1
    predicted=max(candidates,key=lambda c:c['win_probability'])['id']
    brier=sum((c['win_probability']-int(c['id']==winners[0]))**2 for c in candidates) if unique else None
    winner_p=next(c['win_probability'] for c in candidates if c['id']==winners[0])
    return dict(race_id=forecast['id'],name=forecast['name'],category=forecast['category'],polled=bool(forecast['polls_used']),uncontested=len(candidates)==1,candidates=len(candidates),absolute_error_sum=sum(abs(e) for e in errors),squared_error_sum=sum(e*e for e in errors),covered_count=sum(covered),winner_hit=int(predicted==winners[0]) if unique else None,brier=brier,log_loss=-math.log(max(1/(forecast.get('draws',50000)+1),winner_p)) if unique else None,tied=not unique,source_url=actual['source_url'])

def summarize(scores):
    if not scores:return dict(races=0)
    count=sum(s['candidates'] for s in scores)
    unique=[s for s in scores if not s['tied']]
    return dict(races=len(scores),candidates=count,mae_pp=sum(s['absolute_error_sum'] for s in scores)/count,rmse_pp=math.sqrt(sum(s['squared_error_sum'] for s in scores)/count),coverage80=sum(s['covered_count'] for s in scores)/count,winner_accuracy=sum(s['winner_hit'] for s in unique)/len(unique) if unique else None,brier=sum(s['brier'] for s in unique)/len(unique) if unique else None,log_loss=sum(s['log_loss'] for s in unique)/len(unique) if unique else None,unresolved_ties=len(scores)-len(unique))

def evaluate(forecast,actuals):
    actual_byid={a['race_id']:a for a in actuals['races']}
    if len(actual_byid)!=len(actuals['races']):raise ValueError('Duplicate actual race')
    expected={r['id'] for r in forecast['races']}
    if set(actual_byid)!=expected:raise ValueError('Need exact full race coverage')
    scores=[score_race(r,actual_byid[r['id']]) for r in forecast['races']]
    groups={name:summarize([s for s in scores if s['category']==name]) for name in ['region','city','borough']}
    groups.update(polled=summarize([s for s in scores if s['polled']]),unpolled=summarize([s for s in scores if not s['polled']]),uncontested=summarize([s for s in scores if s['uncontested']]),contested=summarize([s for s in scores if not s['uncontested']]))
    return dict(status='complete',forecast_cutoff=forecast['cutoff'],official_results_as_of=actuals.get('as_of'),overall=summarize(scores),groups=groups,races=scores,log_score_floor=1/50001)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('actuals',type=Path);args=parser.parse_args()
    if datetime.now(ZoneInfo('Europe/Bratislava'))<datetime(2026,10,24,20,tzinfo=ZoneInfo('Europe/Bratislava')):
        raise SystemExit('Official post-election evaluation is not available before polls close')
    verify()
    result=evaluate(json.loads((ROOT/'docs/data/forecast.json').read_text()),json.loads(args.actuals.read_text()))
    dump(ROOT/'docs/data/evaluation.json',result)
    dump(ROOT/'docs/data/actuals.json',json.loads(args.actuals.read_text()))
    print(json.dumps(result['overall'],indent=2))
