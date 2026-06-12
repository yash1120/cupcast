"""FastAPI app serving the dashboard and prediction endpoints.

Run:  python -m uvicorn cupcast.api:app --port 8026
"""
import json
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .predict import Predictor

app = FastAPI(title="CupCast", description="ML predictions for the FIFA World Cup 2026",
              version="2.0.0")

DIST = config.ROOT / "frontend" / "dist"  # built React app (falls back to web/)


@lru_cache(maxsize=1)
def get_predictor() -> Predictor:
    return Predictor()


def _load_json(name):
    path = config.MODELS_DIR / name
    if not path.exists():
        raise HTTPException(503, f"{name} missing — run `python -m cupcast.train` "
                                 f"and `python -m cupcast.simulate` first")
    return json.loads(path.read_text())


@app.get("/", include_in_schema=False)
def index():
    if (DIST / "index.html").exists():
        return FileResponse(DIST / "index.html")
    return FileResponse(config.WEB_DIR / "index.html")


@app.get("/ball.svg", include_in_schema=False)
def favicon():
    return FileResponse(DIST / "ball.svg") if (DIST / "ball.svg").exists() \
        else FileResponse(config.WEB_DIR / "index.html")


@app.get("/api/odds")
def odds():
    return JSONResponse(_load_json("simulation.json"))


@app.get("/api/metrics")
def metrics():
    return JSONResponse(_load_json("metrics.json"))


@app.get("/api/teams")
def teams():
    pred = get_predictor()
    return {
        "teams": [
            {"name": t, "display": config.DISPLAY_NAMES.get(t, t),
             "group": config.TEAM_GROUP[t], "host": t in config.HOSTS,
             "elo": round(pred.state["ratings"].get(t, config.ELO_START), 1)}
            for t in sorted(config.WC_TEAMS)
        ]
    }


def _check_teams(pred, *teams):
    known = set(pred.state["ratings"])
    for t in teams:
        if t not in known:
            raise HTTPException(404, f"unknown team: {t}")


@app.get("/api/predict")
def predict(home: str, away: str, neutral: bool = True):
    pred = get_predictor()
    _check_teams(pred, home, away)
    return pred.predict(home, away, neutral)


@app.get("/api/detail")
def detail(home: str, away: str, neutral: bool = True):
    """Scoreline distribution + derived markets (O/U, BTTS, clean sheets)."""
    pred = get_predictor()
    _check_teams(pred, home, away)
    return pred.match_detail(home, away, neutral)


@app.get("/api/weather")
def weather():
    """Open-Meteo forecasts for upcoming fixtures (display context only)."""
    return JSONResponse(_load_json("weather.json"))


@lru_cache(maxsize=1)
def _squads():
    path = config.DATA_DIR / "squads.json"
    if not path.exists():
        raise HTTPException(503, "squads.json missing — run scripts/build_squads.py")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _history():
    import pandas as pd
    return pd.read_csv(config.RESULTS_CSV, parse_dates=["date"]).dropna(subset=["home_score"])


@app.get("/api/squads")
def squads(team: str):
    """Confirmed 26-man squad: position, age, caps, goals, club (Wikipedia)."""
    squad = _squads().get(team)
    if squad is None:
        raise HTTPException(404, f"no squad for: {team}")
    return {"team": team, "players": squad}


if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/api/h2h")
def h2h(a: str, b: str, limit: int = 6):
    """All-time head-to-head record between two teams, plus recent meetings."""
    pred = get_predictor()
    _check_teams(pred, a, b)
    df = _history()
    m = df[((df.home_team == a) & (df.away_team == b)) |
           ((df.home_team == b) & (df.away_team == a))].sort_values("date")
    a_goals = m.apply(lambda r: r.home_score if r.home_team == a else r.away_score, axis=1)
    b_goals = m.apply(lambda r: r.home_score if r.home_team == b else r.away_score, axis=1)
    return {
        "a": a, "b": b, "matches": int(len(m)),
        "a_wins": int((a_goals > b_goals).sum()) if len(m) else 0,
        "b_wins": int((b_goals > a_goals).sum()) if len(m) else 0,
        "draws": int((a_goals == b_goals).sum()) if len(m) else 0,
        "a_goals": int(a_goals.sum()) if len(m) else 0,
        "b_goals": int(b_goals.sum()) if len(m) else 0,
        "recent": [
            {"date": str(r.date.date()), "home": r.home_team, "away": r.away_team,
             "score": f"{int(r.home_score)}-{int(r.away_score)}",
             "tournament": r.tournament}
            for r in m.tail(limit).iloc[::-1].itertuples(index=False)
        ],
    }
