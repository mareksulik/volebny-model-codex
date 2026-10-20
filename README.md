# Samospráva 2026

Verejný experiment s predpoveďou slovenských samosprávnych volieb 24. 10. 2026: 8 krajov, 8 krajských miest a 17 bratislavských mestských častí. Jedno kolo, relatívna väčšina. Za každého kandidáta: odhad percent platných hlasov pre aktívne pole, 80 % interval a pravdepodobnosť výhry.

- Web: https://mareksulik.github.io/volebny-model-codex/
- [Všetkých 33 tabuliek](docs/all.html)
- [Predpoveď JSON](docs/data/forecast.json) · [CSV](docs/data/forecast.csv)
- [Metodika a obmedzenia](METHODOLOGY.md)
- [Zdroje](data/sources.json) · [Prieskumy a vyradenia](data/polls.json) · [Odstúpenia](data/events.json)
- [Spätný test a parametre](data/fit.json) · [Kontrolné súčty](data/LOCK.json)

Výpočet používa overené úradné kandidátky MV SR, historické výsledky ŠÚ SR 2018/2022 a 2017/2022 a doložené miestne prieskumy. V mnohých súbojoch miestny prieskum v zbere chýba; fundamentálny odhad má širokú neistotu. Kurzy sú osobitný benchmark zo sekundárnych prehľadov, nemenia predpoveď. Presný uzáver a okamih zamknutia sú vo verejných dátach. Nejde o záruku presného budúceho výsledku ani o vlastný reprezentatívny prieskum.

Referencia: [Josef Šlerka – Senát 2026](https://github.com/josefslerka/senat-2026-forecast). Model aj kód sú samostatnou implementáciou pre slovenskú jednokolovú voľbu. Codex pripravil výskum a výpočtový experiment na zadanie Mareka Šulika.

## Lokálne overenie

```sh
python3 -m venv venv
venv/bin/python -m unittest discover -s tests -v
venv/bin/python scripts/verify_lock.py
venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Žiadne balíky z pip nie sú potrebné. Publikovaný model odmietne bežný rebuild. Vstupy sú v `data/`, algoritmus v `scripts/`, statický web v `docs/`. Relevantné pôvodné XLSX tabuľky sú archivované; celé veľké ZIP exporty a úplné telá načítaných článkov sa nezverejňujú. Register zberu obsahuje odkazy a kontrolné súčty lokálnych retrievalov, nie celé chránené články.

## Po voľbách

Skopírujte formát z `research/ACTUALS_FORMAT.md`, doplňte kompletné oficiálne počty hlasov zo ŠÚ SR a spustite `venv/bin/python scripts/evaluate.py /cesta/actuals.json`. Skript najprv skontroluje uzamknuté podklady a zapíše iba osobitné povolebné súbory. Publikované odhady zostávajú pôvodné. Metodika vopred určuje MAE, RMSE, pokrytie, úspešnosť víťazov, Brierovo a logaritmické skóre aj členenie súbojov.

Kód má licenciu MIT. Pôvodné texty, čísla a metodika tohto projektu sú dostupné pod CC BY 4.0. Zdrojové materiály MV SR, ŠÚ SR, agentúr a médií si zachovávajú svoje vlastné podmienky; licencia projektu neprelicencuje cudzie články ani grafy.
