"""Fit on 60%, calibrate on 20%, evaluate once on 20% of 2022 contests."""
from collections import defaultdict
import json
import math
from pathlib import Path
from prepare import DATA, dump, key
from model import FEATURES, features, fit, predict, seed_for, simulate

def examples(history):
    grouped=defaultdict(list)
    for row in history:
        grouped[(row['year'],row['office'],row['code'])].append(row)
    output=[]
    for (year,office,code),current in grouped.items():
        if year!=2022 or len(current)<2 or sum(c['votes'] for c in current)<1000:
            continue
        before=grouped.get((2018 if office=='city' else 2017,office,code),[])
        if not before:
            continue
        active=[c for c in current if not c.get('withdrawn',False)]
        if len(active)<2:
            continue
        identity=office+'-'+code
        output.append(dict(id=identity,office=office,name=current[0]['locality'],total_votes=sum(c['votes'] for c in active),candidates=[c['name'] for c in active],x=[features(c,before) for c in active],y=[c['votes']/sum(v['votes'] for v in active) for c in active]))
    return output

def metrics(examples, coefficients, concentration, draws=1500):
    absolute=[]; squared=[]; widths=[]; covered=[]; hits=[]; brier=[]; log_scores=[]
    for e in examples:
        probabilities=predict(e['x'],coefficients)
        stats=simulate(probabilities,concentration,draws,seed_for(e['id']))
        truth=max(range(len(e['y'])),key=e['y'].__getitem__)
        hits.append(max(range(len(probabilities)),key=probabilities.__getitem__)==truth)
        brier.append(sum((s['win_probability']-int(j==truth))**2 for j,s in enumerate(stats)))
        log_scores.append(-math.log(max(1/(draws+1),stats[truth]['win_probability'])))
        for p,y,s in zip(probabilities,e['y'],stats):
            absolute.append(abs(p-y)*100);squared.append(((p-y)*100)**2)
            covered.append(s['low80_pct']<=100*y<=s['high80_pct'])
            widths.append(s['high80_pct']-s['low80_pct'])
    if not examples:
        return dict(races=0)
    return dict(races=len(examples),candidates=len(absolute),mae_pp=sum(absolute)/len(absolute),rmse_pp=math.sqrt(sum(squared)/len(squared)),winner_accuracy=sum(hits)/len(hits),brier=sum(brier)/len(brier),log_loss=sum(log_scores)/len(log_scores),coverage80=sum(covered)/len(covered),mean_interval_width_pp=sum(widths)/len(widths))

def run():
    all_examples=examples(json.loads((DATA/'history.json').read_text()))
    city=[e for e in all_examples if e['office']=='city']
    train=[e for e in city if seed_for(e['id'])%5<3]
    calibration=[e for e in city if seed_for(e['id'])%5==3]
    test=[e for e in city if seed_for(e['id'])%5==4]
    coefficients=fit(train)
    grid=[]
    for concentration in [2,3,4,6,8,12,16,24,32,48,64]:
        score=metrics(calibration,coefficients,concentration,500)
        grid.append(dict(concentration=concentration,**score))
    selected=min(grid,key=lambda r:abs(r['coverage80']-.8))['concentration']
    result=dict(features=FEATURES,coefficients=coefficients,concentration=selected,training_races=len(train),calibration_races=len(calibration),test=metrics(test,coefficients,selected),regional_transfer=metrics([e for e in all_examples if e['office']=='region'],coefficients,selected),calibration_grid=grid,train_ids=[e['id'] for e in train],calibration_ids=[e['id'] for e in calibration],test_ids=[e['id'] for e in test])
    dump(DATA/'fit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k in ['features','coefficients','concentration','training_races','calibration_races','test','regional_transfer']},ensure_ascii=False,indent=2))

if __name__=='__main__':run()
