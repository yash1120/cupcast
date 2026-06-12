"""Monte Carlo simulation of the 2026 World Cup.

Real group fixtures (and any already-played results) come straight from the
dataset; everything not yet played is sampled from the trained models.
Outcome is sampled from the classifier, the scoreline from the Poisson goals
model conditioned on that outcome — so W/D/L odds stay calibrated while goal
difference still drives group tiebreaks.

Run:  python -m cupcast.simulate [n_sims]
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import config
from .features import load_results
from .predict import Predictor
from .weather import VENUES

RNG = np.random.default_rng(7)
ROUND_NAMES = ["r32", "r16", "qf", "sf", "final", "champion"]


# --------------------------------------------------------------- fixtures
def wc_fixtures(df):
    wc = df[(df.tournament == "FIFA World Cup") & (df.date >= config.WC_START)]
    wc = wc[wc.home_team.isin(config.TEAM_GROUP) & wc.away_team.isin(config.TEAM_GROUP)]
    fixtures = []
    for r in wc.itertuples(index=False):
        stadium = VENUES.get(r.city, (None, None, r.city))[2]
        fixtures.append({
            "date": str(r.date.date()),
            "home": r.home_team, "away": r.away_team,
            "city": r.city, "stadium": stadium,
            "neutral": bool(r.neutral),
            "group": config.TEAM_GROUP[r.home_team],
            "played": r.home_score == r.home_score,
            "home_score": None if r.home_score != r.home_score else int(r.home_score),
            "away_score": None if r.away_score != r.away_score else int(r.away_score),
        })
    return fixtures


# ----------------------------------------------------------- match sampling
def sample_score(p, lams, rng):
    """Sample (gh, ga): outcome from classifier, scoreline from Poisson."""
    outcome = rng.choice(3, p=p)
    lh, la = lams
    for _ in range(20):
        gh, ga = rng.poisson(lh), rng.poisson(la)
        if (outcome == 0 and gh > ga) or (outcome == 1 and gh == ga) \
                or (outcome == 2 and gh < ga):
            return gh, ga
    return (1, 0) if outcome == 0 else ((1, 1) if outcome == 1 else (0, 1))


class MatchBook:
    """Precomputed probabilities for every possible WC matchup."""

    def __init__(self, predictor: Predictor, fixtures):
        self.book = {}
        # exact group fixtures as scheduled (respect listed home side / neutrality)
        sched = [(f["home"], f["away"], f["neutral"]) for f in fixtures if not f["played"]]
        probas, lams = predictor.predict_many(sched) if sched else (np.empty((0, 3)), np.empty((0, 2)))
        for (h, a, n), p, l in zip(sched, probas, lams):
            self.book[("fix", h, a)] = (p, l)
        # all unordered pairs for knockout play; hosts keep home advantage
        teams = config.WC_TEAMS
        pairs, queries = [], []
        for i, a in enumerate(teams):
            for b in teams[i + 1:]:
                if b in config.HOSTS and a not in config.HOSTS:
                    queries.append((b, a, False)); pairs.append((a, b, True))
                else:
                    queries.append((a, b, a not in config.HOSTS)); pairs.append((a, b, False))
        probas, lams = predictor.predict_many(queries)
        for (a, b, flipped), p, l in zip(pairs, probas, lams):
            if flipped:  # stored as (b vs a) -> flip back to (a, b) perspective
                p, l = p[::-1].copy(), l[::-1].copy()
            self.book[("pair", a, b)] = (p, l)

    def fixture(self, h, a):
        return self.book[("fix", h, a)]

    def pair(self, a, b):
        """Probabilities from a's perspective for knockout tie a vs b."""
        if ("pair", a, b) in self.book:
            return self.book[("pair", a, b)]
        p, l = self.book[("pair", b, a)]
        return p[::-1], l[::-1]


# ------------------------------------------------------------- group stage
def simulate_groups(fixtures, book, rng):
    pts = defaultdict(float)
    gd = defaultdict(int)
    gf = defaultdict(int)
    for f in fixtures:
        if f["played"]:
            gh, ga = f["home_score"], f["away_score"]
        else:
            p, lams = book.fixture(f["home"], f["away"])
            gh, ga = sample_score(p, lams, rng)
        h, a = f["home"], f["away"]
        pts[h] += 3 if gh > ga else (1 if gh == ga else 0)
        pts[a] += 3 if ga > gh else (1 if gh == ga else 0)
        gd[h] += gh - ga; gd[a] += ga - gh
        gf[h] += gh; gf[a] += ga

    standings = {}
    for g, teams in config.GROUPS.items():
        # points, GD, GF, random jitter for residual ties (h2h not modelled)
        order = sorted(teams, key=lambda t: (pts[t], gd[t], gf[t], rng.random()),
                       reverse=True)
        standings[g] = order
    return standings, pts, gd, gf


def best_thirds(standings, pts, gd, gf, rng):
    thirds = [standings[g][2] for g in config.GROUPS]
    thirds.sort(key=lambda t: (pts[t], gd[t], gf[t], rng.random()), reverse=True)
    return thirds[:8]


def assign_thirds(qualified, rng):
    """Match the 8 best thirds to the 8 third-place bracket slots.

    Backtracking search over the official Annex-C pools; falls back to an
    arbitrary completion if a combination admits no perfect matching.
    """
    slots = [(m, set(spec.split(":")[1]))
             for m, (s1, spec) in sorted(config.R32.items()) if spec.startswith("3:")]
    by_group = {config.TEAM_GROUP[t]: t for t in qualified}
    groups = set(by_group)
    slots = sorted(slots, key=lambda s: len(s[1] & groups))
    assignment = {}

    def solve(i, remaining):
        if i == len(slots):
            return True
        m, pool = slots[i]
        for g in sorted(pool & remaining, key=lambda _: rng.random()):
            assignment[m] = by_group[g]
            if solve(i + 1, remaining - {g}):
                return True
            del assignment[m]
        return False

    if not solve(0, groups):
        rest = list(groups)
        rng.shuffle(rest)
        for (m, _), g in zip(slots, rest):
            assignment.setdefault(m, by_group[g])
    return assignment


# ---------------------------------------------------------------- knockout
def knockout_winner(a, b, book, rng):
    p, _ = book.pair(a, b)
    u = rng.random()
    if u < p[0]:
        return a
    if u < p[0] + p[2]:
        return b
    # draw -> extra time / penalties: renormalize the two win probabilities
    return a if rng.random() < p[0] / (p[0] + p[2]) else b


def simulate_knockout(standings, thirds_map, book, rng, reach):
    slot_team = {}
    for g, order in standings.items():
        slot_team[f"1{g}"], slot_team[f"2{g}"] = order[0], order[1]

    def resolve(spec, match_no):
        return thirds_map[match_no] if spec.startswith("3:") else slot_team[spec]

    winners = {}
    for m, (s1, s2) in config.R32.items():
        a, b = resolve(s1, m), resolve(s2, m)
        reach[a]["r32"] += 1; reach[b]["r32"] += 1
        winners[m] = knockout_winner(a, b, book, rng)
    for rnd, name in ((config.R16, "r16"), (config.QF, "qf"), (config.SF, "sf")):
        nxt = {}
        for m, (m1, m2) in rnd.items():
            a, b = winners[m1], winners[m2]
            reach[a][name] += 1; reach[b][name] += 1
            nxt[m] = knockout_winner(a, b, book, rng)
        winners = nxt
    (m1, m2), = config.FINAL.values()
    a, b = winners[m1], winners[m2]
    reach[a]["final"] += 1; reach[b]["final"] += 1
    champ = knockout_winner(a, b, book, rng)
    reach[champ]["champion"] += 1
    return tuple(sorted((a, b))), champ


def project_bracket(group_stats, book):
    """Deterministic 'chalk' bracket: most likely qualifier fills every slot,
    each tie resolved by whichever side has the higher win probability
    (draws split by relative win strength, mirroring penalty shootouts)."""
    key = lambda t: (group_stats[t]["points"], group_stats[t]["advance"])
    proj = {g: sorted(ts, key=key, reverse=True) for g, ts in config.GROUPS.items()}
    thirds = sorted((proj[g][2] for g in config.GROUPS), key=key, reverse=True)[:8]
    thirds_map = assign_thirds(thirds, np.random.default_rng(0))
    slot_team = {f"{n}{g}": proj[g][n - 1] for g in proj for n in (1, 2)}

    def tie_prob(a, b):
        p, _ = book.pair(a, b)
        return float(p[0] + p[1] * (p[0] / (p[0] + p[2])))

    bracket, winners = {}, {}
    for name, rnd in (("r32", config.R32), ("r16", config.R16), ("qf", config.QF),
                      ("sf", config.SF), ("final", config.FINAL)):
        bracket[name] = []
        for m, (s1, s2) in sorted(rnd.items()):
            if name == "r32":
                a = thirds_map[m] if s2.startswith("3:") else slot_team[s2]
                a, b = slot_team[s1], a
            else:
                a, b = winners[s1], winners[s2]
            pa = tie_prob(a, b)
            winners[m] = a if pa >= 0.5 else b
            bracket[name].append({"match": m, "a": a, "b": b,
                                  "p_a": round(pa, 3), "winner": winners[m]})
    return bracket


# -------------------------------------------------------------------- main
def run(n_sims=config.N_SIMULATIONS, predictor=None, rng=RNG):
    predictor = predictor or Predictor()
    df = load_results()
    fixtures = wc_fixtures(df)
    book = MatchBook(predictor, fixtures)
    n_played = sum(f["played"] for f in fixtures)
    print(f"{len(fixtures)} group fixtures loaded ({n_played} already played, locked in)")

    reach = {t: dict.fromkeys(ROUND_NAMES, 0) for t in config.WC_TEAMS}
    group_stats = {t: {"win_group": 0, "advance": 0, "points": 0.0} for t in config.WC_TEAMS}
    finals = Counter()

    for _ in range(n_sims):
        standings, pts, gd, gf = simulate_groups(fixtures, book, rng)
        thirds = best_thirds(standings, pts, gd, gf, rng)
        thirds_map = assign_thirds(thirds, rng)
        advancing = {standings[g][0] for g in standings} | \
                    {standings[g][1] for g in standings} | set(thirds)
        for g, order in standings.items():
            group_stats[order[0]]["win_group"] += 1
        for t in config.WC_TEAMS:
            group_stats[t]["points"] += pts[t]
            if t in advancing:
                group_stats[t]["advance"] += 1
        final_pair, _ = simulate_knockout(standings, thirds_map, book, rng, reach)
        finals[final_pair] += 1

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_sims": n_sims,
        "results_through": str(df[df.home_score.notna()].date.max().date()),
        "teams": {},
        "fixtures": [],
        "top_finals": [{"pair": list(p), "p": c / n_sims} for p, c in finals.most_common(8)],
        "bracket": project_bracket(group_stats, book),
    }
    for t in config.WC_TEAMS:
        out["teams"][t] = {
            "group": config.TEAM_GROUP[t],
            "elo": round(predictor.state["ratings"].get(t, config.ELO_START), 1),
            "exp_points": round(group_stats[t]["points"] / n_sims, 2),
            "win_group": group_stats[t]["win_group"] / n_sims,
            "advance": group_stats[t]["advance"] / n_sims,
            **{r: reach[t][r] / n_sims for r in ROUND_NAMES},
        }
    for f in fixtures:
        entry = dict(f)
        if not f["played"]:
            p, lams = book.fixture(f["home"], f["away"])
            entry.update(p_home=round(float(p[0]), 4), p_draw=round(float(p[1]), 4),
                         p_away=round(float(p[2]), 4),
                         xg_home=round(float(lams[0]), 2), xg_away=round(float(lams[1]), 2))
        out["fixtures"].append(entry)

    path = config.MODELS_DIR / "simulation.json"
    path.write_text(json.dumps(out, indent=1))
    print(f"Saved {path}")
    top = sorted(out["teams"].items(), key=lambda kv: -kv[1]["champion"])[:10]
    print("Title odds:")
    for t, s in top:
        print(f"  {t:<22}{s['champion']*100:>6.1f}%   (final {s['final']*100:.1f}%, Elo {s['elo']})")
    return out


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else config.N_SIMULATIONS
    run(n)
