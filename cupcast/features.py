"""Feature engineering: turn the raw results history into model matrices."""
from collections import defaultdict, deque

import numpy as np
import pandas as pd

from . import config
from .elo import EloEngine, k_factor

FEATURES = [
    "elo_diff",        # home elo (incl. home advantage if applicable) - away elo
    "elo_home",
    "elo_away",
    "neutral",
    "importance",      # K-factor of the competition, proxies match stakes
    "form_diff",       # rolling points-per-game difference (last FORM_WINDOW)
    "gd_form_diff",    # rolling goal-difference-per-game difference
]


def load_results(path=config.RESULTS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date", kind="stable").reset_index(drop=True)
    return df


def _points(gf, ga):
    return 3.0 if gf > ga else (1.0 if gf == ga else 0.0)


def build_dataset(df: pd.DataFrame):
    """Replay history once, emitting one training row per played match.

    Returns (X, y_outcome, goals_rows, meta) where goals_rows is a per-team
    view (two rows per match) used to fit the Poisson goals model, and meta
    carries dates plus the final engine/form state for prediction time.
    """
    engine = EloEngine()
    matches_played = defaultdict(int)
    form = defaultdict(lambda: deque(maxlen=config.FORM_WINDOW))      # points
    gd_form = defaultdict(lambda: deque(maxlen=config.FORM_WINDOW))   # goal diff

    rows, outcomes, dates = [], [], []
    goal_rows, goal_counts = [], []
    train_start = pd.Timestamp(config.TRAIN_START)

    for row in df.itertuples(index=False):
        played = row.home_score == row.home_score  # not NaN
        h, a = row.home_team, row.away_team
        if played:
            rh, ra = engine.ratings[h], engine.ratings[a]
            adv = 0.0 if row.neutral else config.ELO_HOME_ADV
            eligible = (row.date >= train_start
                        and matches_played[h] >= config.MIN_PRIOR_MATCHES
                        and matches_played[a] >= config.MIN_PRIOR_MATCHES)
            if eligible:
                f_h = np.mean(form[h]) if form[h] else 1.0
                f_a = np.mean(form[a]) if form[a] else 1.0
                g_h = np.mean(gd_form[h]) if gd_form[h] else 0.0
                g_a = np.mean(gd_form[a]) if gd_form[a] else 0.0
                feats = [rh + adv - ra, rh, ra, float(row.neutral),
                         k_factor(row.tournament), f_h - f_a, g_h - g_a]
                rows.append(feats)
                outcomes.append(0 if row.home_score > row.away_score
                                else (1 if row.home_score == row.away_score else 2))
                dates.append(row.date)
                # two attacker-perspective rows for the goals model
                goal_rows.append([rh + adv - ra, f_h - f_a])
                goal_counts.append(min(row.home_score, 8))
                goal_rows.append([ra - (rh + adv), f_a - f_h])
                goal_counts.append(min(row.away_score, 8))
            # update state *after* emitting features
            engine.rate_match(h, a, row.home_score, row.away_score,
                              row.tournament, row.neutral)
            form[h].append(_points(row.home_score, row.away_score))
            form[a].append(_points(row.away_score, row.home_score))
            gd_form[h].append(row.home_score - row.away_score)
            gd_form[a].append(row.away_score - row.home_score)
            matches_played[h] += 1
            matches_played[a] += 1

    X = pd.DataFrame(rows, columns=FEATURES)
    y = np.array(outcomes)
    goals_X = np.array(goal_rows)
    goals_y = np.array(goal_counts, dtype=float)
    meta = {
        "dates": pd.Series(dates),
        "ratings": dict(engine.ratings),
        "form": {t: float(np.mean(v)) for t, v in form.items() if v},
        "gd_form": {t: float(np.mean(v)) for t, v in gd_form.items() if v},
    }
    return X, y, (goals_X, goals_y), meta


def match_features(state, home, away, neutral=True):
    """Single-match feature vector from saved prediction-time state."""
    rh = state["ratings"].get(home, config.ELO_START)
    ra = state["ratings"].get(away, config.ELO_START)
    adv = 0.0 if neutral else config.ELO_HOME_ADV
    f_h = state["form"].get(home, 1.0)
    f_a = state["form"].get(away, 1.0)
    g_h = state["gd_form"].get(home, 0.0)
    g_a = state["gd_form"].get(away, 0.0)
    feats = [rh + adv - ra, rh, ra, float(neutral),
             60.0,  # World Cup importance
             f_h - f_a, g_h - g_a]
    goals_home = [rh + adv - ra, f_h - f_a]
    goals_away = [ra - (rh + adv), f_a - f_h]
    return feats, goals_home, goals_away
