"""Convert original official election tables into auditable model inputs."""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from xlsx_reader import read_xlsx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
CITIES = ['Bratislava', 'Košice', 'Banská Bystrica', 'Nitra', 'Prešov', 'Trnava', 'Trenčín', 'Žilina']
BOROUGHS = ['Staré Mesto', 'Podunajské Biskupice', 'Ružinov', 'Vrakuňa', 'Nové Mesto', 'Rača', 'Vajnory', 'Devín', 'Devínska Nová Ves', 'Dúbravka', 'Karlova Ves', 'Lamač', 'Záhorská Bystrica', 'Jarovce', 'Rusovce', 'Čunovo', 'Petržalka']

def clean(value):
    return ' '.join(str(value).split())

def key(value):
    text = unicodedata.normalize('NFKD', clean(value).casefold())
    return re.sub(r'[^a-z0-9]+', '-', ''.join(c for c in text if not unicodedata.combining(c))).strip('-')

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def rows(name):
    return read_xlsx(DATA / 'raw' / name)[0]

def historic():
    specs = [
        (2018, 'city', 'OSO_2018_tab05.xlsx', ('G','H','J','K','L','M','N','O')),
        (2022, 'city', 'OSO2022_SK_tab05d.xlsx', ('G','H','J','K','L','M','N','O')),
        (2022, 'city', 'OSO2022_SK_tab05x.xlsx', ('A','B','D','E','F','G','H','I')),
        (2022, 'region', 'OSK2022_SK_tab06a.xlsx', ('A','B','D','E','F','G','H','I')),
        (2017, 'region', 'OSK_2017_tab06b.xlsx', ('A','B','D',None,'E','F','G','H')),
    ]
    result = []
    seen = set()
    for year, office, file, cols in specs:
        result.extend(_historic_table(year, office, file, cols, seen))
    return result

def _historic_table(year, office, file, cols, seen):
    output = []
    code, locality, first, last, party, votes, share, note = cols
    for row in rows(file):
        if not row.get(code, '').isdigit() or not row.get(votes, '').isdigit():
            continue
        name = clean(row.get(first, '') + ' ' + (row.get(last, '') if last else ''))
        ballot_column='I' if code=='G' else 'C'
        ballot=int(row[ballot_column])
        identity = (year, office, row[code], ballot)
        if identity in seen:
            continue
        seen.add(identity)
        output.append(dict(year=year, office=office, code=row[code], ballot=ballot, locality=row[locality], name=name, party=row.get(party,''), votes=int(row[votes]), reported_pct=float(row[share]), note=row.get(note,''), source_file=file))
    return output

def registrations_2022():
    specs = [('OSO2022_SK_tab0ad.xlsx', ('G','J','K','N','O','P')), ('OSO2022_SK_tab0ax.xlsx', ('A','D','E','H','I','J')), ('OSK2022_SK_tab0a.xlsx', ('A','D','E','H','J','K'))]
    result = {}
    for file, cols in specs:
        for row in rows(file):
            code, first, last, job, party, note = cols
            if row.get(code,'').isdigit():
                name = clean(row.get(first,'')+' '+row.get(last,''))
                ballot_column='I' if code=='G' else 'C'
                result[(row[code],int(row[ballot_column]))] = dict(job=row.get(job,''), party=row.get(party,''), withdrawn=row.get(note)=='X')
    return result

def candidates_2026():
    races = {}
    for row in rows('OSO26_ZZK-Starosta.xlsx')[3:]:
        locality = clean(row.get('B',''))
        if locality not in CITIES and locality not in ['Bratislava - '+b for b in BOROUGHS]:
            continue
        category = 'city' if locality in CITIES else 'borough'
        rid = category+'-'+key(locality)
        race = races.setdefault(rid, dict(id=rid, name=locality, category=category, candidates=[], source='mv-oso26'))
        name = clean(row['D']+' '+row['E'])
        race['candidates'].append(dict(id=rid+'-'+row['C'], name=name, ballot=int(row['C']), party=clean(row.get('I','')), job=clean(row.get('H','')), active=True))
    for row in rows('VUC26_ZZK-Predseda.xlsx')[3:]:
        locality = clean(row['A']).replace(' samosprávny kraj',' kraj')
        rid = 'region-'+key(locality)
        race = races.setdefault(rid,dict(id=rid,name=locality,category='region',candidates=[],source='mv-vuc26'))
        name = clean(row['C']+' '+row['D'])
        race['candidates'].append(dict(id=rid+'-'+row['B'],name=name,ballot=int(row['B']),party=clean(row.get('J','')),job=clean(row.get('H','')),active=True))
    return list(races.values())

def prepare():
    history = historic()
    regs = registrations_2022()
    for item in history:
        item.update(regs.get((item['code'],item['ballot']),{}) if item['year']==2022 else {})
    grouped = defaultdict(list)
    for item in history:
        grouped[(item['year'],item['office'],item['code'])].append(item)
    for group in grouped.values():
        total = sum(r['votes'] for r in group)
        for r in group:
            r['share'] = r['votes']/total
            r['winner'] = r['votes']==max(x['votes'] for x in group)
    dump(DATA/'history.json',history)
    dump(DATA/'races-register.json',candidates_2026())
    print('Historical rows:',len(history),'Races:',len(candidates_2026()))

if __name__=='__main__':
    prepare()
