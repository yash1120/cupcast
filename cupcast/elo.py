"""World-Football-style Elo rating engine.

Replays the full match history chronologically, recording each team's
pre-match rating so downstream feature building never leaks the result
of the match being predicted.
"""
from collections import defaultdict

from . import config


def k_factor(tournament: str) -> float:
    for needle, k in config.K_FACTORS:
        if needle.lower() in str(tournament).lower():
            return k
    return config.K_DEFAULT


def goal_multiplier(margin: int) -> float:
    """Standard World Football Elo goal-difference multiplier."""
    margin = abs(margin)
    if margin <= 1:
        return 1.0
    if margin == 2:
        return 1.5
    return (11.0 + margin) / 8.0


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


class EloEngine:
    def __init__(self, start=config.ELO_START, home_adv=config.ELO_HOME_ADV):
        self.ratings = defaultdict(lambda: start)
        self.home_adv = home_adv

    def rate_match(self, home, away, home_score, away_score, tournament, neutral):
        """Update ratings for one played match. Returns pre-match ratings."""
        r_home, r_away = self.ratings[home], self.ratings[away]
        adv = 0.0 if neutral else self.home_adv
        exp_home = expected_score(r_home + adv, r_away)
        if home_score > away_score:
            actual = 1.0
        elif home_score < away_score:
            actual = 0.0
        else:
            actual = 0.5
        delta = k_factor(tournament) * goal_multiplier(home_score - away_score) * (actual - exp_home)
        self.ratings[home] = r_home + delta
        self.ratings[away] = r_away - delta
        return r_home, r_away

    def replay(self, df):
        """Replay a chronologically sorted results dataframe.

        Adds elo_home / elo_away columns (pre-match values) and returns df.
        Rows with missing scores (scheduled fixtures) are skipped but still
        annotated with the ratings as of that date.
        """
        pre_home, pre_away = [], []
        for row in df.itertuples(index=False):
            if row.home_score != row.home_score:  # NaN -> unplayed fixture
                pre_home.append(self.ratings[row.home_team])
                pre_away.append(self.ratings[row.away_team])
                continue
            rh, ra = self.rate_match(row.home_team, row.away_team,
                                     row.home_score, row.away_score,
                                     row.tournament, row.neutral)
            pre_home.append(rh)
            pre_away.append(ra)
        df = df.copy()
        df["elo_home"] = pre_home
        df["elo_away"] = pre_away
        return df
