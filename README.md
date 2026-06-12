---
title: CupCast — World Cup 2026 ML Predictor
emoji: ⚽
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: true
license: mit
short_description: ML match forecasts + Monte Carlo simulation of WC2026
---

# ⚽ CupCast — ML forecasts for the FIFA World Cup 2026

End-to-end machine-learning system that predicts every match of the 2026 World Cup and
Monte-Carlo-simulates the full tournament — live title odds, group qualification
probabilities, and a head-to-head predictor for all 48 finalists, served from a FastAPI
dashboard.

Built on **free data only** (no API keys): [martj42/international_results](https://github.com/martj42/international_results),
49,000+ international matches since 1872, which also ships the official 2026 fixture list —
so as real results come in, they get **locked into the simulation** and the odds update.

## How it works

```
results.csv (49k matches)
      │
      ▼
Elo engine ──────────────► pre-match ratings (replayed chronologically, no leakage)
      │
      ▼
Feature builder ─────────► elo diff · home advantage · form · match importance
      │
      ├─► HistGradientBoosting + isotonic calibration ──► P(win/draw/loss)
      └─► Poisson regression ───────────────────────────► expected goals λ
      │
      ▼
Monte Carlo simulator (5,000 tournaments)
      • real group fixtures, played results locked in
      • outcome sampled from classifier, scoreline from Poisson conditioned on it
      • best-thirds rule + official Round-of-32 bracket (Annex C pools)
      │
      ▼
FastAPI + dashboard ─────► title odds · group tables · fixture probabilities · H2H
```

## Quickstart

```bash
pip install -r requirements.txt
python scripts/download_data.py     # fetch latest results (free, no key)
python -m cupcast.train             # train + evaluate, saves artifacts to models/
python -m cupcast.simulate 5000     # Monte Carlo tournament simulation
python -m cupcast.weather           # Open-Meteo forecasts for upcoming fixtures
python scripts/build_squads.py      # 26-man squads from Wikipedia
cd frontend && npm install && npm run build && cd ..   # React + Magic UI dashboard
python -m uvicorn cupcast.api:app --port 8026
# open http://localhost:8026
```

## Frontend

`frontend/` is a React 19 + Vite + Tailwind v4 app using
[Magic UI](https://magicui.design) components (magic-card, number-ticker,
animated-gradient-text, border-beam, shimmer-button, marquee). Four views:

- **Title odds** — championship probabilities chart, most likely finals, H2H predictor
- **Groups** — live FIFA-format tables (P/W/D/L/GD/Pts from real results) + model advance odds
- **Schedule** — the official fixture list, matchday by matchday, with weather and win probabilities
- **Bracket** — projected knockout tree on the official match plan (73–104)

Dev mode: `npm run dev` in `frontend/` proxies `/api` to the local uvicorn.

## Deploy (free)

The `Dockerfile` is fully self-building: it compiles the frontend, downloads the
public dataset, **trains the model, runs the simulation and fetches forecasts at
image build time** — no secrets or API keys anywhere.

**Render** (easiest, free tier): push this repo to GitHub → render.com → *New → Blueprint*
→ select the repo (`render.yaml` does the rest).

**Hugging Face Spaces**: create a Docker Space, then
`git push https://huggingface.co/spaces/<you>/cupcast main` (add
`app_port: 7860` to the Space README frontmatter).

To refresh odds mid-tournament, just trigger a rebuild — the image retrains on the
latest results at build time.

Re-run the three pipeline commands any time during the tournament: newly played
matches are locked in and the odds re-converge around reality.

## Model & evaluation

Time-based hold-out: trained on matches 1990 → 2023, tested on **2,527 internationals
from 2024 onward** (no information from the future leaks into training — Elo and form
features are replayed strictly chronologically).

| Metric (test, 3-way W/D/L) | CupCast | Pure-Elo baseline | Majority class |
|---|---|---|---|
| Accuracy | **60.1%** | 60.2% | 47.5% |
| Log loss | **0.866** | 0.885 | — |
| Brier score | **0.509** | 0.521 | — |

The gradient-boosting model matches Elo on raw accuracy but is meaningfully better
calibrated (log loss / Brier) — which is what matters when probabilities feed a
tournament simulator. ~60% is the practical ceiling for 3-way international football
prediction; bookmaker odds land in the same range.

**Features:** Elo difference (World-Football-Elo style: K by competition importance,
goal-margin multiplier, +80 home advantage), raw Elo ratings, venue neutrality, match
importance, rolling 8-game form (points and goal difference).

**Hosts:** USA, Mexico and Canada genuinely play at home in 2026 — the simulator gives
them home advantage in their own matches; everything else is neutral-venue.

## API

| Endpoint | Returns |
|---|---|
| `GET /` | dashboard |
| `GET /api/odds` | full simulation output (per-team round probabilities, fixtures) |
| `GET /api/predict?home=X&away=Y&neutral=true` | single-match probabilities + xG |
| `GET /api/detail?home=X&away=Y` | scoreline distribution + markets (O/U, BTTS, clean sheets, win-to-nil) |
| `GET /api/weather` | Open-Meteo match-day forecasts per stadium (display context, not a model input) |
| `GET /api/h2h?a=X&b=Y` | all-time head-to-head record + recent meetings (from the results dataset) |
| `GET /api/squads?team=X` | confirmed 26-man squad: position, age, caps, goals, club (Wikipedia) |
| `GET /api/teams` | the 48 finalists with current Elo |
| `GET /api/metrics` | training metrics & data lineage |

## Project structure

```
cupcast/
├── cupcast/
│   ├── config.py      # draw, official bracket, Elo/model constants
│   ├── elo.py         # Elo rating engine
│   ├── features.py    # leakage-free feature replay
│   ├── train.py       # training + evaluation pipeline
│   ├── predict.py     # inference over saved artifacts
│   ├── simulate.py    # Monte Carlo tournament simulator
│   └── api.py         # FastAPI app
├── web/index.html     # dashboard (vanilla JS + Chart.js)
├── tests/             # Elo, bracket, and sampling unit tests (pytest)
├── scripts/download_data.py
└── .github/workflows/ci.yml   # tests + full pipeline smoke test
```

## Match detail & weather

Clicking any upcoming fixture on the dashboard opens a full match panel: win/draw/win
probabilities, expected goals, most likely scorelines, markets, match-day weather at the
actual stadium, the two teams' all-time head-to-head record with recent meetings, and
both confirmed 26-man squads (caps, international goals, club, age — sourced from
Wikipedia via `scripts/build_squads.py`).


`/api/detail` expands any matchup into a full scoreline probability grid: the
independent-Poisson grid is region-rescaled so its win/draw/loss mass matches the
calibrated classifier exactly — most-likely scorelines, over/unders, both-teams-to-score
and clean-sheet probabilities all stay consistent with the headline forecast.

Match-day weather (temperature, rain probability, wind, venue altitude) comes from the
free [Open-Meteo](https://open-meteo.com/) API and is shown as context on every upcoming
fixture. It is deliberately **not** a model feature: the model was never trained on
historical weather, and bolting an untrained adjustment on top would be fake precision.

> ⚠️ **Not betting advice.** The model matches market-level accuracy at best; bookmaker
> margins (5–8%) mean betting on its output loses money in expectation.

## Known simplifications

- Group tiebreaks use points → goal difference → goals for (head-to-head record and
  fair-play points are not modelled).
- Third-place teams are assigned to bracket slots via backtracking over the official
  Annex C pools; FIFA's exact 495-combination table may differ in rare cases.
- Knockout draws resolve by renormalized win probability (no separate extra-time /
  penalty shootout model).
- Squad-level signals (injuries, lineups, market values) are out of scope — the model
  is purely results-based.

## License & data

Code MIT. Match data CC0 from
[martj42/international_results](https://github.com/martj42/international_results).
