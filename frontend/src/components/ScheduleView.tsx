import { Flag, ProbBar, ProbLabels } from "@/components/shared";
import { disp, fmtDate } from "@/lib/flags";
import type { Fixture, OddsData, WeatherMap } from "@/lib/types";

export function ScheduleView({ odds, weather, onMatch }:
  { odds: OddsData; weather: WeatherMap; onMatch: (f: Fixture) => void }) {
  const byDate = new Map<string, Fixture[]>();
  for (const f of odds.fixtures) {
    if (!byDate.has(f.date)) byDate.set(f.date, []);
    byDate.get(f.date)!.push(f);
  }
  const today = new Date().toISOString().slice(0, 10);

  return (
    <div>
      <p className="mb-4 text-sm text-muted">
        The official group-stage schedule, matchday by matchday. Click any match for
        scorelines, markets, squads, head-to-head history and the stadium forecast.
      </p>
      {[...byDate.entries()].map(([date, fixtures]) => (
        <section key={date} className="mb-6">
          <h3 className={`mb-2 flex items-center gap-3 text-sm font-semibold ${date === today ? "text-pitch" : "text-fg"}`}>
            {fmtDate(date)}
            {date === today && (
              <span className="rounded-full bg-pitch/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-pitch">
                today
              </span>
            )}
          </h3>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {fixtures.map((f) => {
              const wx = weather[`${f.date}|${f.city}`];
              return (
                <button key={`${f.home}${f.away}`} onClick={() => onMatch(f)}
                  className="rounded-xl border border-line bg-card p-4 text-left transition-colors hover:border-pitch">
                  <div className="mb-2 flex items-center justify-between text-[11px] text-muted">
                    <span>
                      Group {f.group} · {f.stadium}
                      {!f.neutral && <span className="text-gold"> · home adv</span>}
                    </span>
                    {wx && <span>🌡️ {Math.round(wx.tmax_c)}°C ☔ {wx.precip_prob}%</span>}
                  </div>
                  <div className="flex items-center justify-between text-[15px] font-semibold">
                    <span><Flag team={f.home} /> {disp(f.home)}</span>
                    {f.played
                      ? <span className="font-bold text-gold">{f.home_score} – {f.away_score}</span>
                      : <span className="text-xs text-muted">vs</span>}
                    <span>{disp(f.away)} <Flag team={f.away} /></span>
                  </div>
                  {!f.played && f.p_home !== undefined && (
                    <>
                      <ProbBar className="mt-3" pHome={f.p_home} pDraw={f.p_draw!} pAway={f.p_away!} />
                      <ProbLabels pHome={f.p_home} pDraw={f.p_draw!} pAway={f.p_away!} />
                    </>
                  )}
                  {f.played && (
                    <div className="mt-2 text-[11px] uppercase tracking-wider text-muted">
                      full-time · locked into simulation
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
