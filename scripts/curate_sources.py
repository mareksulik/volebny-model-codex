"""Publish factual source metadata, never scraped copyrighted article bodies."""
import hashlib
import json
from pathlib import Path
from prepare import ROOT, DATA, dump, key

def unwrap(result):
    if result.get('structuredContent'):
        return result['structuredContent']
    try:
        return json.loads(result.get('content',[{}])[0].get('text','{}'))
    except (ValueError,IndexError):
        return {}

def run():
    sources={}
    def add(url,title,kind):
        sources.setdefault(url,dict(id=key(url)[-100:],url=url,title=title,kind=kind,accessed='2026-10-20'))
    for poll in json.loads((DATA/'polls.json').read_text()):
        add(poll['source_url'],poll['agency']+' · '+poll['race_id'],'poll' if poll['included'] else 'excluded-poll')
        if poll.get('sample_source_url'):add(poll['sample_source_url'],'Doplnkový zdroj vzorky','secondary')
    for event in json.loads((DATA/'events.json').read_text()):
        add(event['source_url'],'Odstúpenie · '+event['name'],'event')
    bases=[('mv-oso26','https://www.minv.sk/swift_data/source/verejna_sprava/volby_a_referendum/150_oso/OSO26_ZZK-Starosta.xlsx','Úradný register kandidátov na starostov a primátorov'),('mv-vuc26','https://www.minv.sk/swift_data/source/verejna_sprava/volby_a_referendum/140_vuc/VUC26_ZZK-Predseda.xlsx','Úradný register kandidátov na predsedov krajov')]
    for identity,url,title in bases:
        add(url,title,'official')
        sources[url]['id']=identity
    for office,year in [('oso',2018),('oso',2022),('osk',2017),('osk',2022)]:
        add(f'https://volby.statistics.sk/{office}/{office}{year}/sk/',f'ŠÚ SR · {office.upper()} {year}','official-results')
    add('https://www.minv.sk/?volby-samosprava26','MV SR · termín, informácie a uzáver kampane','official-rules')
    add('https://www.slov-lex.sk/ezbierky/pravne-predpisy/SK/ZZ/2014/180/','Zákon 180/2014 Z. z. · volebné pravidlá','official-rules')
    add('https://github.com/josefslerka/senat-2026-forecast','Josef Šlerka · referencia verejného experimentu','reference')
    for name in ['odds-cities','odds-primary']:
        raw=unwrap(json.loads((ROOT/'research/raw'/f'{name}.json').read_text()))
        add(raw.get('metadata',{}).get('sourceURL') or raw.get('metadata',{}).get('url'), 'Publikované kurzy · '+name,'secondary-odds')
    dump(DATA/'sources.json',list(sources.values()))
    log=[]
    for file in sorted((ROOT/'research/raw').glob('*.json')):
        raw=json.loads(file.read_text()); data=unwrap(raw)
        hits=data.get('data',{}).get('web',[]) if isinstance(data.get('data',{}),dict) else []
        log.append(dict(file=file.name,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),status='error' if raw.get('isError') or data.get('error') or data.get('error_code') else 'retrieved',urls=[dict(url=h['url'],title=h.get('title')) for h in hits],source_url=data.get('metadata',{}).get('sourceURL'),note='Full retrieved article bodies retained locally; excluded from public repository.'))
    dump(DATA/'research-log.json',log)

if __name__=='__main__':run()
