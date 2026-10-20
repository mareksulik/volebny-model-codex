"""Accessible no-JavaScript forecast tables generated from the same snapshot."""
from html import escape
import json
from prepare import ROOT

def run():
    forecast=json.loads((ROOT/'docs/data/forecast.json').read_text())
    sections=[]
    for race in forecast['races']:
        rows=[]
        for c in sorted(race['candidates'],key=lambda c:(not c['active'],-c['estimate_pct'])):
            name=escape(c['name'])+(' (odstúpenie)' if not c['active'] else '')
            rows.append(f'<tr><td>{name}</td><td>{c["estimate_pct"]:.2f} %</td><td>{c["low80_pct"]:.1f} – {c["high80_pct"]:.1f} %</td><td>≈ {100*c["win_probability"]:.1f} %</td></tr>')
        notes=' '.join(race['notes'])
        sections.append(f'<section class="all-race" id="{race["id"]}"><h2>{escape(race["name"])}</h2><p>{escape(race["category"])} · {len(race["polls_used"])} meraní</p><div class="table-wrap benchmark-scroll"><table><thead><tr><th>Kandidát</th><th>Hlasy</th><th>80 % interval</th><th>Výhra</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div><p>{escape(notes)}</p></section>')
    html=f'<!doctype html><html lang="sk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Všetkých 33 súbojov · Samospráva 2026</title><link rel="stylesheet" href="style.css"></head><body><main class="page"><header><a class="brand" href="./">Samospráva 2026</a><a href="./">Interaktívny výber</a></header><h1>Všetkých 33 súbojov</h1><p>Dátový uzáver {escape(forecast["cutoff"])}. Podiely platných hlasov pre aktívne pole. Výsledky sú odhady s neistotou; znak ≈ upozorňuje aj na konečný počet simulácií.</p>{"".join(sections)}<footer><a href="data/forecast.json">JSON</a><a href="data/forecast.csv">CSV</a><a href="./#method">Metodika a zdroje</a></footer></main></body></html>'
    (ROOT/'docs/all.html').write_text(html)

if __name__=='__main__':run()
