"""Single-round compositional forecast. Standard library only."""
import hashlib
import math
import random
import re
from datetime import date
from prepare import key

FEATURES = ['previous_share', 'previous_winner', 'coalition_size', 'deputy', 'elected_role', 'independent']

def normalize(values):
    if not values or any(not math.isfinite(x) or x < 0 for x in values) or sum(values) <= 0:
        raise ValueError('Expected nonnegative finite values with positive sum')
    total = sum(values)
    return [x / total for x in values]

def features(candidate, previous):
    matches = [p for p in previous if key(p['name'])==key(candidate['name'])]
    old = matches[0] if len(matches)==1 else {}
    job = key(candidate.get('job',''))
    party = candidate.get('party','')
    independent = bool(re.search(r'nezávis|NEKA|NK/',party,re.I))
    parties = min(6, len(re.split('[,;]',party))) if not independent else 0
    return [old.get('share',0)*2, float(old.get('winner',False)), math.log1p(parties), float('zastup' in job or 'viceprim' in job), float(any(w in job for w in ['poslan','starost','primator','minister','predseda-samosprav','predsednicka-samosprav'])),float(independent)]

def predict(xs, coefficients):
    logits = [sum(a*b for a,b in zip(x,coefficients)) for x in xs]
    peak = max(logits)
    return normalize([math.exp(v-peak) for v in logits])

def fit(examples, iterations=700):
    if not examples:
        raise ValueError('No training examples')
    coefficients = [0.0]*len(FEATURES)
    for _ in range(iterations):
        gradient = [0.0]*len(coefficients)
        for example in examples:
            probabilities = predict(example['x'], coefficients)
            for x,p,y in zip(example['x'],probabilities,example['y']):
                for j,value in enumerate(x):
                    gradient[j] += (p-y)*value/len(examples)
        coefficients = [b-0.7*(g+0.015*b) for b,g in zip(coefficients,gradient)]
    return coefficients

def seed_for(identity, seed=20261020):
    return seed + int(hashlib.sha256(identity.encode()).hexdigest()[:8],16)

def quantile(sorted_values, q):
    index = (len(sorted_values)-1)*q
    lower = int(index)
    upper = min(lower+1,len(sorted_values)-1)
    return sorted_values[lower]+(sorted_values[upper]-sorted_values[lower])*(index-lower)

def simulate(probabilities, concentration, draws=50000, seed=20261020, transfer_mass=0, transfer_prior=None):
    probabilities = normalize(probabilities)
    if not math.isfinite(concentration) or concentration <= 0 or not isinstance(draws,int) or draws < 100:
        raise ValueError('Invalid simulation parameters')
    if len(probabilities)==1:
        return [dict(estimate_pct=100.0,low80_pct=100.0,high80_pct=100.0,win_probability=1.0)]
    rng = random.Random(seed)
    if not 0 <= transfer_mass < 1:
        raise ValueError('Invalid transfer mass')
    transfer_prior = normalize(transfer_prior or probabilities)
    known = normalize([max(0,p-transfer_mass*t) for p,t in zip(probabilities,transfer_prior)]) if transfer_mass else probabilities
    samples = [[] for _ in probabilities]
    wins = [0.0]*len(probabilities)
    for _ in range(draws):
        sample = normalize([rng.gammavariate(max(1e-5,p*concentration),1) if p else 0 for p in known])
        if transfer_mass:
            transfer = normalize([rng.gammavariate(max(1e-5,p*2),1) for p in transfer_prior])
            sample = [(1-transfer_mass)*s+transfer_mass*t for s,t in zip(sample,transfer)]
        maximum = max(sample)
        leaders = [j for j,v in enumerate(sample) if v==maximum]
        for j in leaders:
            wins[j] += 1/len(leaders)
        for j,value in enumerate(sample):
            samples[j].append(value*100)
    return [dict(estimate_pct=p*100,low80_pct=quantile(sorted(s),.1),high80_pct=quantile(sorted(s),.9),win_probability=w/draws) for p,s,w in zip(probabilities,samples,wins)]

def blend_polls(prior, candidates, polls, cutoff, withdrawn_names=()):
    """Published percentages are pseudo-counts, not raw survey microdata."""
    alpha = [5*p for p in prior]
    used = []
    unallocated = 0
    for poll in polls:
        end = date.fromisoformat(poll.get('fieldwork_end') or poll['published'])
        if end > cutoff or date.fromisoformat(poll['published']) > cutoff:
            raise ValueError('Poll after cutoff')
        if not poll.get('included',False):
            continue
        mapping = {key(n):p for n,p in poll['shares'].items()}
        expected = {key(c['name']) for c in candidates}
        removed = set(mapping)-expected
        if expected-set(mapping) or not removed.issubset({key(n) for n in withdrawn_names}):
            raise ValueError('Poll candidate field differs from active field: '+poll['id'])
        normalize(list(mapping.values()))
        known_total = sum(mapping.values())
        undecided = poll.get('undecided_pct',0)
        total = known_total+undecided
        mass = (sum(mapping[n] for n in removed)+undecided)/total
        if sum(mapping[n] for n in removed)/known_total > .20:
            raise ValueError('Changed candidate field exceeds 20 percent')
        values = [mapping[key(c['name'])]/total+mass*p for c,p in zip(candidates,prior)]
        age = (cutoff-end).days
        n = poll.get('n_decided') or poll.get('n_local')
        n_effective = (min(200,n/2) if n else 25)*2**(-age/30) * poll.get('quality_weight',1)
        alpha = [a+n_effective*v for a,v in zip(alpha,values)]
        unallocated += n_effective*mass
        used.append(dict(id=poll['id'],effective_n=n_effective,withdrawn_mass=mass))
    return normalize(alpha),used,unallocated/sum(alpha)

def market_probabilities(odds):
    if not odds or any(not math.isfinite(v) or v<=1 for v in odds):
        raise ValueError('Decimal odds must exceed one')
    return normalize([1/v for v in odds])
