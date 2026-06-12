import { useEffect, useState } from "react";

import { AnimatedGradientText } from "@/components/magicui/animated-gradient-text";
import { Marquee } from "@/components/magicui/marquee";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { BracketView } from "@/components/BracketView";
import { GroupsView } from "@/components/GroupsView";
import { H2HPicker } from "@/components/H2HPicker";
import { MatchModal } from "@/components/MatchModal";
import { OddsChart } from "@/components/OddsChart";
import { ScheduleView } from "@/components/ScheduleView";
import { Disclaimer, Flag } from "@/components/shared";
import { getMetrics, getOdds, getTeams, getWeather } from "@/lib/api";
import { disp, pct } from "@/lib/flags";
import type { Fixture, Metrics, OddsData, TeamInfo, WeatherMap } from "@/lib/types";

type Tab = "overview" | "groups" | "schedule" | "bracket";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "🏆 Title odds" },
  { id: "groups", label: "📋 Groups" },
  { id: "schedule", label: "📅 Schedule" },
  { id: "bracket", label: "🗺️ Bracket" },
];

export default function App() {
  const [odds, setOdds] = useState<OddsData | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [teams, setTeams] = useState<TeamInfo[]>([]);
  const [weather, setWeather] = useState<WeatherMap>({});
  const [tab, setTab] = useState<Tab>("overview");
  const [match, setMatch] = useState<Fixture | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getOdds(), getMetrics(), getTeams(), getWeather().catch(() => null)])
      .then(([o, m, t, w]) => {
        setOdds(o); setMetrics(m); setTeams(t.teams);
        setWeather(w?.forecasts ?? {});
      })
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <main className="mx-auto max-w-xl p-10 text-center">
        <h1 className="text-xl font-bold">⚽ CupCast</h1>
        <p className="mt-4 text-sm text-loss">{error}</p>
        <p className="mt-2 text-sm text-muted">
          Is the API running? Train + simulate first, then start uvicorn.
        </p>
      </main>
    );
  }
  if (!odds || !metrics) {
    return <main className="p-20 text-center text-muted">Loading forecasts…</main>;
  }

  const topTeams = Object.entries(odds.teams).sort((a, b) => b[1].champion - a[1].champion);

  return (
    <>
      <header className="bg-[radial-gradient(ellipse_at_top,#14203a_0%,transparent_70%)] px-5 pb-6 pt-10 text-center">
        <AnimatedGradientText speed={1.4} colorFrom="#22d37f" colorTo="#f5c542"
          className="text-4xl font-extrabold tracking-tight">
          ⚽ CupCast
        </AnimatedGradientText>
        <p className="mt-2 text-sm text-muted">
          Machine-learning forecasts for the FIFA World Cup 2026 · trained on 49,000+
          internationals since 1872
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-2.5 text-xs">
          <span className="rounded-full border border-line bg-card px-3.5 py-1.5 text-muted">
            🎲 <NumberTicker value={odds.n_sims} className="font-semibold text-fg" /> simulations
          </span>
          <span className="rounded-full border border-line bg-card px-3.5 py-1.5 text-muted">
            🎯 held-out accuracy{" "}
            <NumberTicker value={+(metrics.model.accuracy * 100).toFixed(1)} decimalPlaces={1}
              className="font-semibold text-fg" />%
          </span>
          <span className="rounded-full border border-line bg-card px-3.5 py-1.5 text-muted">
            🧠 <NumberTicker value={metrics.training_samples} className="font-semibold text-fg" /> training matches
          </span>
          <span className="rounded-full border border-line bg-card px-3.5 py-1.5 text-muted">
            📊 results through <b className="text-fg">{odds.results_through}</b>
          </span>
        </div>
      </header>

      <div className="border-y border-line/60 bg-card2/40 py-2">
        <Marquee pauseOnHover className="[--duration:55s] [--gap:2.5rem] text-sm">
          {topTeams.slice(0, 16).map(([t, s]) => (
            <span key={t} className="text-muted">
              <Flag team={t} size={16} /> {disp(t)} <b className="text-pitch">{pct(s.champion)}</b>
            </span>
          ))}
        </Marquee>
      </div>

      <nav className="sticky top-0 z-40 flex justify-center gap-1.5 border-b border-line/60 bg-background/85 px-4 py-3 backdrop-blur">
        {TABS.map(({ id, label }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              tab === id
                ? "bg-pitch/15 text-pitch"
                : "text-muted hover:bg-card hover:text-fg"}`}>
            {label}
          </button>
        ))}
      </nav>

      <main className="mx-auto max-w-6xl px-5 pb-16 pt-8">
        {tab === "overview" && (
          <div>
            <p className="mb-4 text-sm text-muted">
              Probability of lifting the trophy on 19 July 2026 — every team's full path
              simulated through the official bracket with the best-thirds rule.
            </p>
            <OddsChart odds={odds} />
            <div className="mt-8 grid gap-6 md:grid-cols-2">
              <div>
                <h2 className="mb-3 text-lg font-bold">Most likely finals</h2>
                {odds.top_finals.map((f) => (
                  <div key={f.pair.join()} className="flex items-center justify-between border-t border-card2 py-2 text-sm">
                    <span>
                      <Flag team={f.pair[0]} size={16} /> {disp(f.pair[0])}
                      <span className="mx-2 text-muted">vs</span>
                      <Flag team={f.pair[1]} size={16} /> {disp(f.pair[1])}
                    </span>
                    <span className="tabular-nums text-muted">{pct(f.p)}</span>
                  </div>
                ))}
              </div>
              <div>
                <h2 className="mb-3 text-lg font-bold">Head-to-head predictor</h2>
                <H2HPicker teams={teams} />
              </div>
            </div>
          </div>
        )}
        {tab === "groups" && <GroupsView odds={odds} onMatch={setMatch} />}
        {tab === "schedule" && <ScheduleView odds={odds} weather={weather} onMatch={setMatch} />}
        {tab === "bracket" && <BracketView odds={odds} />}

        <footer className="mt-14 text-center text-xs text-muted">
          Calibrated gradient boosting + Elo features · test log-loss{" "}
          {metrics.model.log_loss.toFixed(3)} (Elo baseline {metrics.elo_baseline.log_loss.toFixed(3)}) ·
          data: <a className="text-pitch hover:underline"
            href="https://github.com/martj42/international_results">martj42/international_results</a> ·
          weather: Open-Meteo · squads: Wikipedia · built with scikit-learn, FastAPI, React &amp; Magic UI
          <Disclaimer />
        </footer>
      </main>

      {match && <MatchModal fixture={match} weather={weather} onClose={() => setMatch(null)} />}
    </>
  );
}
