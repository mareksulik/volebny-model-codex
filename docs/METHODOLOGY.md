# Samospráva 2026: predregistrovaná špecifikácia

Verzia 1.0.0. Voľby 24. 10. 2026. Publikačný limit 21. 10. 2026 o 23:59 Europe/Bratislava. Presný uzáver vstupov je vo `docs/data/forecast.json`; okamih uzamknutia v `data/LOCK.json`. Autorstvo výpočtového experimentu: Codex v spolupráci s Marekom Šulikom. Nie je to vlastný reprezentatívny prieskum.

## Od predpokladov k modelu

Neoverený predpoklad, že každý zaregistrovaný kandidát zostáva aktívny, vyvracajú doložené odstúpenia. Predpoklad, že celoslovenská vzorka patrí každému kraju, je nesprávny: regionálne podvzorky sú menšie. Kurz na víťazstvo meria inú veličinu než podiel hlasov. Minulý podiel ani výkon funkcie negarantujú dnešnú podporu; ich predikčná hodnota sa overuje historicky.

Overené vstupné fakty sú úradné registrácie MV SR a počty hlasov ŠÚ SR. Každý volič odovzdáva v danej voľbe jeden hlas kandidátovi; podiely pre celé aktívne pole tvoria 100 %. V jednom kole rozhoduje relatívna väčšina. Z týchto obmedzení vyplýva spoločné rozdelenie podielov na simplexe a porovnanie všetkých kandidátov v každej simulácii. Parametre predikcie a neistoty sú odhadované alebo výslovne predpokladané, nie overené prírodné konštanty.

Prevzatie dvojkolovej senátnej logiky by nesprávne riešilo postup a druhé kolo. Tento model má jediné kolo a funkciu víťaza argmax podielu. Zo Šlerkovho verejného experimentu preberá transparentnú dátovú stopu, zverejnenie pred výsledkami a následné skórovanie, nie senátny mechanizmus ani jeho numerické odhady.

## Rozsah a identifikácia

8 predsedov krajov, 8 primátorov krajských miest, 17 starostov bratislavských mestských častí. Úradné XLSX registre majú v tomto rozsahu 148 mien. Stav po 9 zdrojmi uvádzaných odstúpeniach má 139 aktívnych kandidátov. Registrácia je primárny zdroj; odstúpenia sú uvedené ako mediálne doložené udalosti, nie ako nezávisle potvrdený právny stav všetkých komisií. Predpoveď je týmto stavom kandidátky podmienená.

Identita 2026: funkcia + lokalita + poradové číslo na lístku. Historická identita: rok + typ volieb + kód obce/kraja + poradové číslo. Zhodné mená sa nezlučujú. Medzi rokmi sa podpora prenáša len pri jednoznačnom mene v rovnakom súboji; pri nejednoznačnosti sa individuálna minulosť nepoužije. Lörinc a Lörincz sú rôzni kandidáti. Normalizácia medzier a diakritiky je technická pomôcka; nie voľné približné párovanie osôb.

Historické podiely sa znovu počítajú z počtov hlasov. Každý riadok sa kontroluje proti percentu ŠÚ SR s toleranciou 0,02 p. b. pre publikované zaokrúhlenie. Riadky obsahujúce výsledky sa odlišujú od registrácií a odstúpení. Zaznamenané chyby importu a opravy sú v `research/QA.md`.

## Fundamentálny odhad

Podiel pre kandidáta i je softmax(X_i × beta). Príznaky: dvojnásobok podielu v predchádzajúcich voľbách, predchádzajúce víťazstvo, log(1 + počet strán v aktuálnej koalícii, strop 6), deklarovaná funkcia zástupcu/viceprimátora, deklarovaná volená alebo verejná funkcia a nezávislá kandidatúra. Funkcie sa čítajú z úradných registrácií; nejde o úplnú biografiu. Počet strán sa získava jednoduchým rozdelením textu koalície podľa čiarok a bodkočiarok. Nie je to model ideológie, straníckych preferencií alebo prenosu celej koalície.

Beta minimalizuje priemernú krížovú entropiu skutočných podielov hlasov po súbojoch s L2 penalizáciou 0,015. Každý súboj má rovnakú váhu. Používa sa 700 gradientných krokov s krokom 0,7. Minulý víťaz je predikčný príznak, nie identifikovaný kauzálny efekt obhajcu. Napríklad historický víťaz po prerušení výkonu funkcie je stále historickým víťazom. Škandály a kontext, ktoré model neobsahuje, nemožno interpretovať ako nulový vplyv.

Tréningové dáta: komunálne súboje 2018 → 2022 s aspoň 1 000 platnými hlasmi v roku 2022, aspoň 2 aktívnymi kandidátmi a dostupnou minulosťou. Rozdelenie vychádza z `(20261020 + int(SHA256('city-' + kod)[:8], 16)) % 5`: zvyšky 0–2 tréning, 3 kalibrácia, 4 test. Regionálne voľby 2017 → 2022 nie sú tréningom ani kalibráciou, ale samostatným malým testom prenosu. Test sa nepoužíva na výber koncentrácie. Číselné výsledky, koeficienty a identifikátory množín obsahuje `data/fit.json`.

## Zaradenie prieskumov

Všetky zaradenia a vyradenia sú v `data/polls.json`. Vyžaduje sa úplné kandidátne pole alebo doložené odstúpenie, identifikovateľná agentúra a zdroj. Neúplné pole Focus Košice, neúplný dostupný prieskum Trnavy a Vox Prešov bez overenej vzorky a terénnych dátumov sú vyradené. Hypotetické jarné bratislavské kandidátky a internetové ankety sa nepoužívajú. Nepoužíva sa parlamentný prieskum ako miestna podpora kandidáta.

Základ má 5 pseudopozorovaní rozdelených podľa fundamentálneho odhadu. Pre meranie sa váha rovná `min(200, n / 2) × 2^(-vek_dni / 30) × quality_weight`. n je počet rozhodnutých, ak je známy, inak miestna vzorka. Pri SCIO sa 1 025 celoslovenských respondentov nepoužije pre každý kraj: nezverejnené miestne n znamená fixný základ 25 pseudopozorovaní pred starnutím. Podobná politika platí pri neznámom miestnom n v článku AKO. Týchto 25 je metodické rozhodnutie, nie tvrdenie o skutočnej vzorke.

Pri chýbajúcich terénnych dátumoch je `fieldwork_end = null`; pre časový pokles sa používa publikovanie a kvalitatívna váha 0,5. Tá istá polovičná váha je priznaná kandidátskemu prieskumu Focus Nitra. Parametre nie sú odhadnuté z historických chýb agentúr. Viac zdrojov opisujúcich rovnaké meranie sa nesčítava ako nové merania. Publikovanie aj dostupný koniec zberu musia byť najneskôr k uzáveru.

Body z grafov SCIO boli ručne odčítané z primárnych obrázkov; originály sú ponechané lokálne, verejne sa zdieľajú faktické percentá a odkazy. Ipsos Košice uvádza u Székelyho menej ako 1 %; do vstupu je vložený zvyšok 0 % po sčítaní zaokrúhlených hodnôt ostatných kandidátov. Je to explicitná imputácia, nie presne nameraná nula. Základ aj neistota ponechávajú tejto kandidatúre kladnú podporu. Pri Chlustinovej má článok AKO 1,2 % v texte a 1,1 % v grafe; použitý je údaj textu a normalizácia zaokrúhleného súčtu.

## Nerozhodnutí a odstúpenia

Ak sa uvádzajú nerozhodnutí v rovnakom menovateli, nevymažú sa mechanickým prepočtom rozhodnutých. Ich masa a masa odstúpených kandidátov sa eviduje ako nepriradená. Pre stredný odhad sa rozdelí podľa fundamentálneho základu. V simuláciách sa príslušná vážená masa presúva podľa samostatného Dirichlet(2 × základ) scenára. Kandidát, ktorého odstúpený podporil, automaticky nedostáva všetky jeho hlasy. Pri viac než 20 % podpory odstúpených by zaradenie zlyhalo. Presun je predpoklad, nie zistený prechod voličov; rozhodnutí v inom meraní nemajú automaticky rovnakú účasť.

Odstúpené mená zostávajú v exporte označené ako neaktívne s 0 % hlasov pre aktívne pole a 0 % výhry. Nevydáva sa to za prognózu počtu zakrúžkovaných neaktívnych mien. Pri 4 súbojoch s jediným aktívnym kandidátom ide o podmienených 100 % platných hlasov a výhry: bez modelovania odkladu, zrušenia alebo nulového hlasovania.

## Neistota a simulácie

Každý súboj má 50 000 spoločných simulácií podielov, vždy so súčtom 100 %. Semeno: `20261020 + int(SHA256(race_id)[:8], 16)`. Fundamentálny benchmark má osobitné semeno s predponou `baseline-`.

Koncentrácia fundamentálneho Dirichletovho rozdelenia sa vyberá z 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64 podľa najbližšieho pokrytia 80 % na kalibračnej množine (500 simulácií pri výbere; oddelený test 1 500). Pri prieskumoch je koncentrácia `min(80, základná koncentrácia + súčet účinných váh)`. Strop zanecháva nenulovú neistotu aj pri početnom meraní, ale nie je dôkazom správneho pokrytia. Táto časť nebola kalibrovaná na starších miestnych prieskumoch; možné spoločné chyby agentúr, mobilizácia a zmeny do volieb môžu byť väčšie.

V každej simulácii vyhráva najvyšší podiel. Výstup je stredná hodnota podielu, 10. a 90. percentil (marginálny 80 % predikčný interval) a frekvencia výhier. Bodový odhad je analytická stredná hodnota deklarovaného rozdelenia; nemusí byť jeho mediánom. Marginálne hranice sa nesčítavajú na 100 %. Presná rovnosť skutočných celočíselných hlasov, účasť a zrušenie voľby nie sú modelované. Numerická štandardná chyba frekvencie pri 50 % je asi 0,22 p. b.; 0/50 000 simulovaných výhier nedokazuje nemožnosť.

## Trhový benchmark

`data/odds.json` zachytáva 14 zverejnených prehľadov trhov. Ide o sekundárne agregátory zachytené 20. 10. 2026, nie priame potvrdenie aktuálnych ponúk kancelárií. Za každú kompletnú kanceláriu sa počíta `(1 / kurz_i) / sum(1 / kurz_j)` pre celé aktívne pole. Neúplné trhy sa nenormalizujú. Kurz výhry sa nepoužíva ako podiel hlasov a benchmark nemení hlavnú predpoveď. Priame stávky ani finančné transakcie sa nevykonali.

## Uzamknutie a vyhodnotenie

Pred termínom sa spustia testy, vytvorí sa `LOCK.json` so SHA-256 vstupov, algoritmu, testov, metodiky a verejných výstupov. Verejný Git commit a tag `forecast-final-v1` ukotvia kontrolné súčty. Nie je to nezmeniteľnosť voči vlastníkovi repozitára: zmenu však možno porovnať s pôvodným verejným commitom. Skript odmietne prepísať uzamknutie aj vytvárať predpoveď po publikačnom limite. Automatické aktualizovanie predpovedí počas moratória sa nevykonáva.

Po voľbách sa importujú oficiálne počty hlasov s pôvodnými kandidátnymi identifikátormi a odkazom na ŠÚ SR. Primárne metriky sú MAE a RMSE v p. b. cez kandidátov, 80 % pokrytie cez kandidátov, úspešnosť najpravdepodobnejšieho víťaza, súčet štvorcových chýb pravdepodobností víťazstva (multikategóriové Brierovo skóre, rozsah 0–2) priemerovaný cez súboje a záporný log pravdepodobnosti skutočného víťaza. Pre log je vopred stanovená numerická podlaha 1/50 001; nuly z konečného Monte Carlo sa nepovažujú za metafyzickú nemožnosť.

Výstup sa člení podľa typu volieb, dostupnosti prieskumu a súťažnosti. Jediní kandidáti sa uvádzajú samostatne; úspešnosť víťazov sa nesmie opierať iba o ich automatické zásahy. Pri rovnosti hlasov sa označí nerozhodnutý súboj, neudelia sa rozdelené fiktívne výhry. Pôvodné podiely sa netunujú podľa výsledku. Povolebné súbory `actuals.json` a `evaluation.json` sú oddelené od uzamknutého manifestu.

## Reprodukcia

Python 3.14, iba štandardná knižnica. Na novom checkoute vytvorte `python3 -m venv venv`. `scripts/verify_lock.py` overí publikované súbory. Na diagnostickú reprodukciu použite `build.create_forecast(original_cutoff, original_draws)` a porovnajte numerické polia s toleranciou 1e-8 pre rozdiely matematických knižníc. Bežný build uzamknutú snímku odmietne prepísať. Pre pôvodnú dátovú prípravu sú potrebné archivované relevantné XLSX tabuľky; veľké pôvodné ZIP exporty sú lokálny cache a sú vylúčené z Gitu.
