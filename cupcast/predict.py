"""Prediction interface over the saved artifacts."""
import numpy as np
import joblib
import pandas as pd

from . import config
from .features import FEATURES, match_features

_GOALS_SCALE = np.array([400.0, 3.0])


class Predictor:
    def __init__(self, path=None):
        bundle = joblib.load(path or config.MODELS_DIR / "model.joblib")
        self.model = bundle["model"]
        self.goals_model = bundle["goals_model"]
        self.state = bundle["state"]

    def predict(self, home, away, neutral=True):
        feats, gh, ga = match_features(self.state, home, away, neutral)
        X = pd.DataFrame([feats], columns=FEATURES)
        p = self.model.predict_proba(X)[0]
        lam = self.goals_model.predict(np.array([gh, ga]) / _GOALS_SCALE)
        lam = np.clip(lam, 0.15, 5.0)
        return {
            "home": home, "away": away, "neutral": bool(neutral),
            "p_home": float(p[0]), "p_draw": float(p[1]), "p_away": float(p[2]),
            "exp_goals_home": float(lam[0]), "exp_goals_away": float(lam[1]),
            "elo_home": round(self.state["ratings"].get(home, config.ELO_START), 1),
            "elo_away": round(self.state["ratings"].get(away, config.ELO_START), 1),
        }

    def predict_many(self, fixtures):
        """fixtures: iterable of (home, away, neutral). Vectorized for speed."""
        rows, goal_rows = [], []
        for home, away, neutral in fixtures:
            feats, gh, ga = match_features(self.state, home, away, neutral)
            rows.append(feats)
            goal_rows.extend([gh, ga])
        X = pd.DataFrame(rows, columns=FEATURES)
        probas = self.model.predict_proba(X)
        lams = self.goals_model.predict(np.array(goal_rows) / _GOALS_SCALE)
        lams = np.clip(lams, 0.15, 5.0).reshape(-1, 2)
        return probas, lams

    def match_detail(self, home, away, neutral=True, max_goals=8):
        """Full scoreline distribution and derived markets for one match.

        Builds an independent-Poisson scoreline grid, then rescales the
        win/draw/loss regions so they sum exactly to the calibrated
        classifier probabilities — scorelines stay consistent with the
        headline W/D/L forecast.
        """
        base = self.predict(home, away, neutral)
        lh, la = base["exp_goals_home"], base["exp_goals_away"]
        from scipy.stats import poisson  # local import; scipy ships with sklearn
        g = np.arange(max_goals + 1)
        grid = np.outer(poisson.pmf(g, lh), poisson.pmf(g, la))
        grid /= grid.sum()  # fold tail mass (>max_goals) back in

        hg, ag = np.indices(grid.shape)
        for mask, p in ((hg > ag, base["p_home"]), (hg == ag, base["p_draw"]),
                        (hg < ag, base["p_away"])):
            region = grid[mask].sum()
            if region > 0:
                grid[mask] *= p / region

        flat = [(int(i), int(j), float(grid[i, j]))
                for i in g for j in g]
        flat.sort(key=lambda x: -x[2])
        total = hg + ag
        detail = {
            **base,
            "top_scorelines": [{"score": f"{i}-{j}", "p": round(p, 4)}
                               for i, j, p in flat[:8]],
            "markets": {
                "over_1_5": float(grid[total >= 2].sum()),
                "over_2_5": float(grid[total >= 3].sum()),
                "over_3_5": float(grid[total >= 4].sum()),
                "btts": float(grid[(hg > 0) & (ag > 0)].sum()),
                "clean_sheet_home": float(grid[ag == 0].sum()),
                "clean_sheet_away": float(grid[hg == 0].sum()),
                "win_to_nil_home": float(grid[(hg > ag) & (ag == 0)].sum()),
                "win_to_nil_away": float(grid[(ag > hg) & (hg == 0)].sum()),
            },
            "scoreline_grid": [[round(float(grid[i, j]), 5) for j in range(6)]
                               for i in range(6)],
        }
        return detail

    def wc_neutral(self, team):
        """At WC2026 the three hosts genuinely play at home."""
        return team not in config.HOSTS
