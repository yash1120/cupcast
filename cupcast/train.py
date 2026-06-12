"""Training pipeline: fit, evaluate against baselines, persist artifacts.

Run:  python -m cupcast.train
"""
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import accuracy_score, log_loss

from . import config
from .elo import expected_score
from .features import FEATURES, build_dataset, load_results


def _brier(y_true, proba):
    onehot = np.eye(3)[y_true]
    return float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))


def evaluate(model, X_test, y_test):
    proba = model.predict_proba(X_test)
    return {
        "accuracy": float(accuracy_score(y_test, proba.argmax(axis=1))),
        "log_loss": float(log_loss(y_test, proba, labels=[0, 1, 2])),
        "brier": _brier(y_test, proba),
    }


def elo_baseline(X_test, y_test):
    """Pure-Elo baseline: P(win) from the Elo expectation, fixed draw rate."""
    exp = np.array([expected_score(r.elo_home + (0 if r.neutral else 0), r.elo_away)
                    for r in X_test.itertuples(index=False)])
    # elo_diff already includes home advantage; recompute from it directly
    exp = 1.0 / (1.0 + 10.0 ** (-X_test["elo_diff"].to_numpy() / 400.0))
    p_draw = np.full_like(exp, 0.24)  # historical international draw rate
    proba = np.column_stack([exp * (1 - p_draw), p_draw, (1 - exp) * (1 - p_draw)])
    proba /= proba.sum(axis=1, keepdims=True)
    return {
        "accuracy": float(accuracy_score(y_test, proba.argmax(axis=1))),
        "log_loss": float(log_loss(y_test, proba, labels=[0, 1, 2])),
        "brier": _brier(y_test, proba),
    }


def main():
    print("Loading results...")
    df = load_results()
    n_played = int(df.home_score.notna().sum())
    print(f"  {len(df):,} rows ({n_played:,} played matches, "
          f"{df.date.min().date()} .. {df.date.max().date()})")

    print("Replaying history / building features...")
    X, y, (goals_X, goals_y), meta = build_dataset(df)
    dates = meta["dates"]
    print(f"  {len(X):,} training samples since {config.TRAIN_START}")

    split = pd.Timestamp(config.TEST_SPLIT)
    train_idx, test_idx = (dates < split).to_numpy(), (dates >= split).to_numpy()
    print(f"  time split @ {config.TEST_SPLIT}: "
          f"{train_idx.sum():,} train / {test_idx.sum():,} test")

    def make_model():
        base = HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
            l2_regularization=1.0, random_state=42)
        return CalibratedClassifierCV(base, method="isotonic", cv=3)

    print("Fitting outcome model (held-out evaluation)...")
    model = make_model()
    model.fit(X[train_idx], y[train_idx])
    metrics_model = evaluate(model, X[test_idx], y[test_idx])
    metrics_elo = elo_baseline(X[test_idx], y[test_idx])
    base_rate = float(np.bincount(y[test_idx], minlength=3).max() / test_idx.sum())
    print(f"  model:        {metrics_model}")
    print(f"  elo baseline: {metrics_elo}")
    print(f"  majority-class accuracy: {base_rate:.3f}")

    print("Refitting on all data...")
    final_model = make_model()
    final_model.fit(X, y)

    print("Fitting Poisson goals model...")
    goals_model = PoissonRegressor(alpha=1e-4, max_iter=300)
    goals_model.fit(goals_X / np.array([400.0, 3.0]), goals_y)  # crude scaling

    config.MODELS_DIR.mkdir(exist_ok=True)
    state = {"ratings": meta["ratings"], "form": meta["form"], "gd_form": meta["gd_form"]}
    joblib.dump({"model": final_model, "goals_model": goals_model,
                 "features": FEATURES, "state": state}, config.MODELS_DIR / "model.joblib")

    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_rows": int(len(df)),
        "played_matches": n_played,
        "last_result_date": str(df[df.home_score.notna()].date.max().date()),
        "training_samples": int(len(X)),
        "test_window": f"{config.TEST_SPLIT} onward ({int(test_idx.sum())} matches)",
        "model": metrics_model,
        "elo_baseline": metrics_elo,
        "majority_class_accuracy": base_rate,
    }
    (config.MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    wc_elos = {t: round(meta["ratings"].get(t, config.ELO_START), 1)
               for t in config.WC_TEAMS}
    (config.MODELS_DIR / "wc_ratings.json").write_text(
        json.dumps(dict(sorted(wc_elos.items(), key=lambda kv: -kv[1])), indent=2))

    print(f"Artifacts saved to {config.MODELS_DIR}")
    print("Top 10 Elo (WC teams):")
    for t, r in list(sorted(wc_elos.items(), key=lambda kv: -kv[1]))[:10]:
        print(f"  {t:<22}{r:>8.1f}")


if __name__ == "__main__":
    main()
