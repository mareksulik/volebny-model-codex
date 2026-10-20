'use strict';
const state = { category: 'city', selected: 'city-bratislava', forecast: null, polls: [], sources: [], odds: [] };
const q = (s) => document.querySelector(s);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const number = (value, decimals = 1) => Number(value).toLocaleString('sk-SK', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
const probability = (p, exact = false) => `${!exact && (p === 0 || p === 1) ? '≈ ' : ''}${number(p * 100)} %`;
const type = { city: 'Primátor mesta', region: 'Predseda samosprávneho kraja', borough: 'Starosta mestskej časti' };
const link = (url, title) => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>`;

function renderSelection() {
  const races = state.forecast.races.filter((r) => r.category === state.category);
  if (!races.some((r) => r.id === state.selected)) state.selected = races[0].id;
  q('#race').innerHTML = races.map((r) => `<option value="${escapeHtml(r.id)}">${escapeHtml(r.name)}</option>`).join('');
  q('#race').value = state.selected;
  document.querySelectorAll('[data-category]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.category === state.category)));
  q('#coverage').textContent = `${races.length} súbojov · ${races.filter((r) => r.polls_used.length).length} s miestnym meraním v modeli`;
  renderRace();
}

function renderRace() {
  const race = state.forecast.races.find((r) => r.id === state.selected);
  q('#race-name').textContent = race.name;
  q('#race-type').textContent = `${type[race.category]} · jednokolová voľba`;
  const active = race.candidates.filter((c) => c.active);
  const rows = [...race.candidates].sort((a, b) => Number(b.active) - Number(a.active) || b.estimate_pct - a.estimate_pct);
  q('#candidates').innerHTML = rows.map((c) => `<tr class="${c.active ? '' : 'withdrawn'}"><td><strong>${escapeHtml(c.name)}</strong><span class="candidate-party">${c.active ? escapeHtml(c.party) : 'Odstúpenie uvádza zdroj · mimo aktívneho poľa'}</span></td><td data-label="Odhad hlasov">${number(c.estimate_pct, 2)} %</td><td data-label="80 % interval">${number(c.low80_pct)} – ${number(c.high80_pct)} %${c.active ? `<div class="range" aria-hidden="true"><span style="left:${c.low80_pct}%;width:${c.high80_pct - c.low80_pct}%"></span><i style="left:${c.estimate_pct}%"></i></div>` : ''}</td><td data-label="Výhra">${probability(c.win_probability, !c.active || active.length === 1)}</td></tr>`).join('');
  q('#race-notes').innerHTML = race.notes.map((s) => `<p>${escapeHtml(s)}</p>`).join('');
  const used = state.polls.filter((p) => race.polls_used.some((u) => u.id === p.id));
  const registry = state.sources.find((s) => s.id === race.source);
  const historyOffice = race.category === 'region' ? 'osk' : 'oso';
  q('#race-sources').innerHTML = `<li>${registry ? link(registry.url, 'Úradná kandidátka MV SR') : 'Úradná kandidátka MV SR'}</li><li>${link(`https://volby.statistics.sk/${historyOffice}/${historyOffice}2022/sk/`, 'Výsledky 2022 · ŠÚ SR')} a fundamentálny model</li>${used.map((p) => `<li>${link(p.source_url, `${p.agency} · ${p.fieldwork_end || 'publikované ' + p.published}`)}${p.n_local ? ` · n = ${number(p.n_local, 0)}` : ' · miestne n nezverejnené'}${p.fieldwork_end ? '' : ' · terénny dátum chýba'}</li>`).join('')}`;
  renderBenchmark(race);
  q('#race-content').setAttribute('aria-busy', 'false');
  history.replaceState(null, '', `#${race.id}`);
}

function renderBenchmark(race) {
  const market = state.odds.find((o) => o.race_id === race.id);
  const active = race.candidates.filter((c) => c.active);
  const books = market ? [...new Set(Object.values(market.quotes).flatMap((v) => Object.keys(v)))] : [];
  const complete = books.filter((book) => active.every((c) => market.quotes[c.id]?.[book] > 1));
  const totals = Object.fromEntries(complete.map((book) => [book, active.reduce((sum, c) => sum + 1 / market.quotes[c.id][book], 0)]));
  const rows = active.map((c) => `<tr><td>${escapeHtml(c.name)}</td><td>${number(c.fundamental_pct)} %</td><td>${probability(c.fundamental_win_probability, active.length === 1)}</td>${complete.map((book) => `<td>${number(100 / market.quotes[c.id][book] / totals[book])} %</td>`).join('')}</tr>`).join('');
  q('#benchmark').innerHTML = `<p>Fundamentálny model bez prieskumov. ${market ? link(market.source_url, 'Kurzy tretej strany') + ' · zachytené ' + market.observed_date : 'Kurzový benchmark v zbere chýba.'} ${market && !complete.length ? 'Žiadny načítaný trh nepokrýva celé aktívne pole; pravdepodobnosti z neho nepočítame.' : ''}</p><div class="table-wrap benchmark-scroll"><table><thead><tr><th>Kandidát</th><th>Základ hlasy</th><th>Základ výhra</th>${complete.map((b) => `<th>${escapeHtml(b)} výhra</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div><p>Trhové pravdepodobnosti sú normalizované osobitne za každú kanceláriu. Nemajú vplyv na hlavnú predpoveď. Ich kalibrácia ani aktuálnosť nebola overená.</p>`;
}

function renderEvaluation(evaluation) {
  const labels = { overall: 'Všetky súboje', region: 'Kraje', city: 'Krajské mestá', borough: 'Mestské časti', polled: 'S prieskumom', unpolled: 'Bez prieskumu', contested: 'Viacerí kandidáti', uncontested: 'Jediný kandidát' };
  const metrics = { overall: evaluation.overall, ...evaluation.groups };
  const rows = Object.entries(metrics).filter(([, v]) => v.races).map(([key, value]) => `<tr><td>${labels[key] || escapeHtml(key)}</td><td>${value.races}</td><td>${number(value.mae_pp)}</td><td>${number(value.rmse_pp)}</td><td>${number(value.coverage80 * 100)} %</td><td>${value.winner_accuracy === null ? '—' : number(value.winner_accuracy * 100) + ' %'}</td><td>${value.brier === null ? '—' : number(value.brier, 3)}</td></tr>`).join('');
  const races = evaluation.races.map((r) => `<tr><td>${link(r.source_url, r.name)}</td><td>${number(r.absolute_error_sum / r.candidates)}</td><td>${r.tied ? 'Rovnosť hlasov' : r.winner_hit ? 'Správne' : 'Nesprávne'}</td></tr>`).join('');
  q('#evaluation-output').innerHTML = `<div class="table-wrap benchmark-scroll"><table><thead><tr><th>Skupina</th><th>Súboje</th><th>MAE p. b.</th><th>RMSE p. b.</th><th>80 % pokrytie</th><th>Víťaz</th><th>Brier</th></tr></thead><tbody>${rows}</tbody></table></div><details><summary>Porovnanie jednotlivých súbojov</summary><table><thead><tr><th>Súboj a oficiálny zdroj</th><th>MAE p. b.</th><th>Víťaz</th></tr></thead><tbody>${races}</tbody></table></details><p>${link('data/actuals.json', 'Skutočné počty hlasov')} · ${link('data/evaluation.json', 'Úplné metriky vrátane logaritmického skóre')}</p>`;
}

async function init() {
  try {
    const files = ['forecast.json', 'polls.json', 'sources.json', 'odds.json'];
    const data = await Promise.all(files.map(async (file) => { const response = await fetch(`data/${file}`); if (!response.ok) throw new Error(file); return response.json(); }));
    [state.forecast, state.polls, state.sources, state.odds] = data;
    const hash = location.hash.slice(1);
    const selected = state.forecast.races.find((r) => r.id === hash);
    if (selected) { state.selected = selected.id; state.category = selected.category; }
    const timestamp = new Date(state.forecast.cutoff).toLocaleString('sk-SK', { timeZone: 'Europe/Bratislava', dateStyle: 'medium', timeStyle: 'short' });
    q('#status').textContent = `Dátový uzáver: ${timestamp} (Europe/Bratislava) · ${state.forecast.status === 'locked' ? 'Uzamknutá' : 'Pracovná'} experimentálna predpoveď`;
    const test = state.forecast.backtest;
    q('#backtest').textContent = `Oddelený test 2022: ${test.races} súbojov · MAE ${number(test.mae_pp)} p. b. · správny víťaz ${number(100 * test.winner_accuracy)} % · pokrytie 80 % intervalov ${number(100 * test.coverage80)} %. Tieto hodnoty sa týkajú fundamentálneho základu, nie celej agregácie prieskumov 2026.`;
    q('#source-list').innerHTML = state.sources.filter((s) => s.url).map((s) => `<li>${link(s.url, s.title)} <span class="source-kind">${escapeHtml(s.kind)} · prístup ${s.accessed}</span></li>`).join('');
    q('#race').addEventListener('change', (event) => { state.selected = event.target.value; renderRace(); });
    document.querySelectorAll('[data-category]').forEach((button) => button.addEventListener('click', () => { state.category = button.dataset.category; renderSelection(); }));
    renderSelection();
    const lockResponse = await fetch('data/LOCK.json');
    if (lockResponse.ok) { const lock = await lockResponse.json(); q('#lock-status').textContent = `Uzamknuté ${lock.locked_at}. SHA-256 predpovede: ${lock.files['docs/data/forecast.json']}.`; }
    const evaluationResponse = await fetch('data/evaluation.json');
    if (evaluationResponse.ok) { const evaluation = await evaluationResponse.json(); if (evaluation.status === 'complete') { q('#evaluation-status').textContent = 'Vyhodnotenie pôvodnej uzamknutej snímky'; renderEvaluation(evaluation); } }
  } catch (error) {
    q('#race-type').textContent = 'Dáta sa nepodarilo načítať. Obnovte stránku alebo použite statický prehľad.';
    q('#race-content').classList.add('error');
    q('#race-content').setAttribute('aria-busy', 'false');
  }
}
init();
