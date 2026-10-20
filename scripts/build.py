"""Generate a reproducible pre-election snapshot; refuse to overwrite a lock."""
import argparse
from collections import defaultdict
import copy
import csv
from datetime import date,datetime
import json
from pathlib import Path
import shutil
from zoneinfo import ZoneInfo
from prepare import DATA, ROOT, dump, key
from model import blend_polls, features, normalize, predict, seed_for, simulate

DEADLINE = datetime(2026,10,21,23,59,tzinfo=ZoneInfo('Europe/Bratislava'))

def apply_events(races,events):
    output=copy.deepcopy(races)
    for event in events:
        race=next(r for r in output if r['id']==event['race_id'])
        matches=[c for c in race['candidates'] if key(c['name'])==key(event['name'])]
        if len(matches)!=1:raise ValueError('Ambiguous event identity')
        matches[0].update(active=False,event_source=event['source_url'])
    return output

def forecast_race(race,history,parameters,polls,cutoff,draws=50000):
    active=[c for c in race['candidates'] if c['active']]
    if not active:raise ValueError('No active candidates')
    office='region' if race['category']=='region' else 'city'
    before=[r for r in history if r['year']==2022 and r['office']==office and key(r['locality'])==key(race['name'])]
    prior=predict([features(c,before) for c in active],parameters['coefficients'])
    local_polls=[p for p in polls if p['race_id']==race['id']]
    mean,used,transfer=blend_polls(prior,active,local_polls,cutoff,[c['name'] for c in race['candidates'] if not c['active']])
    concentration=min(80,parameters['concentration']+sum(p['effective_n'] for p in used))
    stats=simulate(mean,concentration,draws,seed_for(race['id']),transfer,prior)
    baseline=simulate(prior,parameters['concentration'],draws,seed_for('baseline-'+race['id']))
    result=copy.deepcopy(race)
    for candidate in result['candidates']:
        if not candidate['active']:
            candidate.update(estimate_pct=0,low80_pct=0,high80_pct=0,win_probability=0,fundamental_pct=0,fundamental_win_probability=0)
            continue
        i=next(i for i,c in enumerate(active) if c['id']==candidate['id'])
        candidate.update(stats[i],fundamental_pct=prior[i]*100,fundamental_win_probability=baseline[i]['win_probability'])
        matches=[r for r in before if key(r['name'])==key(candidate['name'])]
        old=matches[0] if len(matches)==1 else None
        candidate['previous_pct']=old['share']*100 if old else None
    result.update(polls_used=used,concentration=concentration,transfer_mass=transfer,history_year=2022,has_matching_history=bool(before),evidence='polls+fundamentals' if used else 'fundamentals',notes=[])
    if not used:result['notes'].append('Bez zaradeného miestneho prieskumu. Slabší fundamentálny odhad; široké intervaly sú podstatnou súčasťou výsledku.')
    if len(active)==1:result['notes'].append('Jediný aktívny kandidát: 100 % podmienené platným konaním volieb a aspoň jedným platným hlasom. Model neodhaduje zrušenie volieb ani volebnú účasť.')
    if transfer:result['notes'].append('Časť meranej podpory je neistá pre odstúpenia alebo nerozhodnutých. Presun je modelový scenár, nie nameraný prechod voličov.')
    return result

def create_forecast(cutoff,draws=50000):
    history=json.loads((DATA/'history.json').read_text())
    parameters=json.loads((DATA/'fit.json').read_text())
    events=json.loads((DATA/'events.json').read_text())
    for event in events:
        if any(event.get(field) and event[field]>cutoff[:10] for field in ['observed_date','event_date']):
            raise ValueError('Event after cutoff')
    races=apply_events(json.loads((DATA/'races-register.json').read_text()),events)
    polls=json.loads((DATA/'polls.json').read_text())
    results=[forecast_race(r,history,parameters,polls,date.fromisoformat(cutoff[:10]),draws) for r in races]
    return dict(version='1.0.0',cutoff=cutoff,election_date='2026-10-24',deadline=DEADLINE.isoformat(),rule='single-round-plurality',interval='marginal central 80 percent predictive interval',draws_per_race=draws,seed=20261020,status='draft',races=results,backtest=parameters['test'],regional_transfer=parameters['regional_transfer'])

def export(forecast, directory):
    directory.mkdir(parents=True,exist_ok=True)
    dump(directory/'forecast.json',forecast)
    fields=['race_id','race','category','candidate_id','candidate','active','estimate_pct','low80_pct','high80_pct','win_probability','fundamental_pct','fundamental_win_probability']
    with (directory/'forecast.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
        for race in forecast['races']:
            for c in race['candidates']:
                row={f:c.get(f) for f in fields}
                row.update(race_id=race['id'],race=race['name'],category=race['category'],candidate_id=c['id'],candidate=c['name'])
                writer.writerow(row)

def run():
    parser=argparse.ArgumentParser();parser.add_argument('--cutoff',default=None);parser.add_argument('--draws',default=50000,type=int);parser.add_argument('--output',type=Path,default=ROOT/'docs/data');args=parser.parse_args()
    args.cutoff=args.cutoff or datetime.now(ZoneInfo('Europe/Bratislava')).replace(microsecond=0).isoformat()
    if (ROOT/'data/LOCK.json').exists():raise SystemExit('Forecast is locked. Use verify_lock.py; never rebuild published forecasts.')
    if datetime.now(ZoneInfo('Europe/Bratislava'))>DEADLINE:raise SystemExit('Pre-election publication deadline passed')
    if datetime.fromisoformat(args.cutoff)>DEADLINE:raise SystemExit('Cutoff after publication deadline')
    if datetime.fromisoformat(args.cutoff)>datetime.now(ZoneInfo('Europe/Bratislava')):raise SystemExit('Cutoff cannot be in the future')
    forecast=create_forecast(args.cutoff,args.draws)
    export(forecast,args.output)
    for name in ['polls.json','events.json','sources.json','fit.json','research-log.json','odds.json']:
        if (DATA/name).exists():shutil.copyfile(DATA/name,args.output/name)
    print('Forecast:',len(forecast['races']),'races,',sum(len(r['candidates']) for r in forecast['races']),'registered candidates')

if __name__=='__main__':run()
