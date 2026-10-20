# Import skutočných výsledkov

Vyplniť až po voľbách z oficiálnych výsledkov ŠÚ SR. Identifikátory sú presne z uzamknutého `docs/data/forecast.json`. Každý z pôvodne aktívnych kandidátov musí mať celočíselný nezáporný počet hlasov, každý z 33 súbojov musí byť prítomný raz. Ak bola kandidatúra následne zrušená, zaznamenať to v zdrojových poznámkach a 0 iba podľa oficiálneho výsledku; neskrývať zmeny pôvodného poľa.

```json
{
  "as_of": "2026-10-25T10:00:00+01:00",
  "races": [
    {
      "race_id": "city-bratislava",
      "source_url": "https://volby.statistics.sk/...",
      "votes": {"city-bratislava-1": 0, "city-bratislava-3": 0, "city-bratislava-4": 0, "city-bratislava-5": 0}
    }
  ]
}
```

Nuly sú iba ilustrácia formátu, nie skutočné výsledky. Import s nulovým celkovým počtom hlasov alebo neúplným rozsahom zlyhá. Pri neuskutočnenom súboji alebo právne nevyriešenom výsledku neuvádzať vymyslené hlasy; hodnotenie zostane neúplné a treba výslovne uviesť dôvod. `evaluate.py` úmyselne vyžaduje úplné oficiálne dáta.
