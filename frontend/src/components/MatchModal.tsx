import { useEffect, useState } from "react";

import { Disclaimer, Flag, MarketList, ProbBar, ProbLabels, ScoreList, SectionTitle } from "@/components/shared";
import { getDetail, getH2H, getSquad } from "@/lib/api";
import { disp } from "@/lib/flags";
import type { Fixture, H2H, MatchDetail, Player, WeatherMap } from "@/lib/types";

const POS_ORDER = ["Goalkeeper", "Defender", "Midfielder", "Forward"];

function Squad({ team, players }: { team: string; players: Player[] }) {
  const topScorers = new Set(
    [...players].sort((a, b) => b.goals - a.goals).slice(0, 3)
      .filter((p) => p.goals > 0).map((p) => p.name));
  const byPos = new Map<string, Player[]>();
  for (const p of players) {
    if (!byPos.has(p.pos)) byPos.set(p.pos, []);
    byPos.get(p.pos)!.push(p);
  }
  return (
    <div className="max-h-96 overflow-y-auto rounded-xl border border-card2 p-3">
      <h5 className="sticky -top-3 -mt-3 bg-card pb-1 pt-3 text-sm font-semibold">
        <Flag team={team} /> {disp(team)} — 26-man squad
      </h5>
      {POS_ORDER.map((pos) => byPos.has(pos) && (
        <div key={pos}>
          <div className="pb-0.5 pt-2 text-[11px] uppercase tracking-wider text-pitch">{pos}s</div>
          {byPos.get(pos)!.sort((a, b) => b.caps - a.caps).map((p) => (
            <div key={p.name}
              className="grid grid-cols-[22px_1fr_56px_30px] gap-1.5 border-t border-card2 py-1 text-xs tabular-nums">
              <span className="text-right text-muted">{p.no ?? ""}</span>
              <span className={`truncate ${topScorers.has(p.name) ? "text-gold" : ""}`}>
                {p.name} <span className="text-muted">· {p.club}{p.age ? ` · ${p.age}` : ""}</span>
              </span>
              <span className="text-right text-muted">{p.caps} caps</span>
              <span className="text-right text-muted">{p.goals}g</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function History({ h2h, home, away }: { h2h: H2H; home: string; away: string }) {
  if (h2h.matches === 0) {
    return <p className="text-sm text-muted">These two teams have never met in a recognised international.</p>;
  }
  const chip = (label: string, value: number | string) => (
    <span className="rounded-lg bg-card2 px-3 py-1.5 text-xs text-muted">
      {label} <b className="text-fg">{value}</b>
    </span>
  );
  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-2">
        {chip("meetings", h2h.matches)}
        {chip(`${disp(home)} wins`, h2h.a_wins)}
        {chip("draws", h2h.draws)}
        {chip(`${disp(away)} wins`, h2h.b_wins)}
        {chip("goals", `${h2h.a_goals}–${h2h.b_goals}`)}
      </div>
      {h2h.recent.map((m) => (
        <div key={m.date} className="flex justify-between gap-3 border-t border-card2 py-1.5 text-xs text-muted">
          <span>{m.date}</span>
          <span className="font-semibold text-fg">{disp(m.home)} {m.score} {disp(m.away)}</span>
          <span className="truncate text-right">{m.tournament}</span>
        </div>
      ))}
    </div>
  );
}

export function MatchModal({ fixture, weather, onClose }:
  { fixture: Fixture; weather: WeatherMap; onClose: () => void }) {
  const [detail, setDetail] = useState<MatchDetail | null>(null);
  const [h2h, setH2H] = useState<H2H | null>(null);
  const [squads, setSquads] = useState<[Player[], Player[]] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    Promise.all([
      getDetail(fixture.home, fixture.away, fixture.neutral),
      getH2H(fixture.home, fixture.away),
      getSquad(fixture.home).catch(() => null),
      getSquad(fixture.away).catch(() => null),
    ]).then(([d, h, sh, sa]) => {
      if (!live) return;
      setDetail(d); setH2H(h);
      setSquads([sh?.players ?? [], sa?.players ?? []]);
    }).catch((e) => live && setError(String(e)));
    return () => { live = false; };
  }, [fixture]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const wx = weather[`${fixture.date}|${fixture.city}`];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-[#04070ec7] p-4 backdrop-blur-sm md:p-10"
      onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="mx-auto max-w-3xl rounded-2xl border border-line bg-card p-6">
        <button onClick={onClose}
          className="float-right rounded-lg border border-line bg-card2 px-3 py-1 text-sm text-muted hover:text-fg">
          ✕ close
        </button>
        <div className="flex items-center gap-3 text-xl font-bold">
          <span><Flag team={fixture.home} size={24} /> {disp(fixture.home)}</span>
          <span className="text-sm font-normal text-muted">vs</span>
          <span>{disp(fixture.away)} <Flag team={fixture.away} size={24} /></span>
        </div>
        <p className="mb-4 mt-1 text-xs text-muted">
          {fixture.date} · Group {fixture.group} · {fixture.stadium}
          {wx && <> · 🌡️ {Math.round(wx.tmin_c)}–{Math.round(wx.tmax_c)}°C · ☔ {wx.precip_prob}% · 💨 {Math.round(wx.wind_kmh)} km/h
            {wx.elevation_m > 1000 && <> · ⛰️ {wx.elevation_m} m</>}</>}
          {!fixture.neutral && <span className="text-gold"> · home advantage</span>}
        </p>

        {error && <p className="text-sm text-loss">Failed to load: {error}</p>}
        {!detail && !error && <p className="text-sm text-muted">Loading match detail…</p>}

        {detail && (
          <>
            {fixture.played ? (
              <div className="rounded-xl border border-card2 bg-card2/50 p-4 text-center">
                <span className="text-2xl font-bold text-gold">
                  {fixture.home_score} – {fixture.away_score}
                </span>
                <div className="mt-1 text-xs uppercase tracking-wider text-muted">
                  full-time · this result is locked into every simulation
                </div>
              </div>
            ) : (
              <>
                <ProbBar pHome={detail.p_home} pDraw={detail.p_draw} pAway={detail.p_away} />
                <ProbLabels pHome={detail.p_home} pDraw={detail.p_draw} pAway={detail.p_away} />
              </>
            )}
            <p className="mt-2 text-xs text-muted">
              Expected goals {detail.exp_goals_home.toFixed(2)} – {detail.exp_goals_away.toFixed(2)} ·
              Elo {detail.elo_home} vs {detail.elo_away}
            </p>

            <div className="mt-5 grid gap-6 md:grid-cols-2">
              <div>
                <SectionTitle>Most likely scorelines</SectionTitle>
                <ScoreList scorelines={detail.top_scorelines} />
              </div>
              <div>
                <SectionTitle>Markets</SectionTitle>
                <MarketList markets={detail.markets} home={fixture.home} away={fixture.away} />
              </div>
            </div>

            {h2h && (
              <div className="mt-6">
                <SectionTitle>Head-to-head history</SectionTitle>
                <History h2h={h2h} home={fixture.home} away={fixture.away} />
              </div>
            )}

            {squads && (squads[0].length > 0 || squads[1].length > 0) && (
              <div className="mt-6">
                <SectionTitle>Confirmed squads — caps &amp; international goals</SectionTitle>
                <p className="mb-2 text-xs text-muted">
                  <span className="text-gold">Gold names</span> = squad's top international scorers.
                  Per-player vs-team splits aren't in any free dataset — figures are full careers.
                </p>
                <div className="grid gap-4 md:grid-cols-2">
                  {squads[0].length > 0 && <Squad team={fixture.home} players={squads[0]} />}
                  {squads[1].length > 0 && <Squad team={fixture.away} players={squads[1]} />}
                </div>
              </div>
            )}
            <Disclaimer />
          </>
        )}
      </div>
    </div>
  );
}
