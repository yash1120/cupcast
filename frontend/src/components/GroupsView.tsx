import { MagicCard } from "@/components/magicui/magic-card";
import { Flag } from "@/components/shared";
import { disp, pct } from "@/lib/flags";
import type { Fixture, OddsData } from "@/lib/types";

interface Row {
  team: string;
  p: number; w: number; d: number; l: number;
  gf: number; ga: number; pts: number;
  advance: number;
  expPoints: number;
}

function standings(odds: OddsData, group: string): Row[] {
  const teams = Object.entries(odds.teams)
    .filter(([, s]) => s.group === group)
    .map(([t, s]) => ({
      team: t, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0,
      advance: s.advance, expPoints: s.exp_points,
    }));
  const byName = new Map(teams.map((r) => [r.team, r]));
  for (const f of odds.fixtures) {
    if (!f.played || f.group !== group) continue;
    const h = byName.get(f.home)!, a = byName.get(f.away)!;
    const hs = f.home_score!, as = f.away_score!;
    h.p++; a.p++; h.gf += hs; h.ga += as; a.gf += as; a.ga += hs;
    if (hs > as) { h.w++; a.l++; h.pts += 3; }
    else if (hs < as) { a.w++; h.l++; a.pts += 3; }
    else { h.d++; a.d++; h.pts++; a.pts++; }
  }
  return teams.sort((x, y) =>
    y.pts - x.pts || (y.gf - y.ga) - (x.gf - x.ga) || y.gf - x.gf || y.advance - x.advance);
}

function posStyle(i: number): string {
  if (i < 2) return "border-l-2 border-l-pitch";       // direct qualification zone
  if (i === 2) return "border-l-2 border-l-gold/60";   // best-thirds zone
  return "border-l-2 border-l-transparent";
}

export function GroupsView({ odds, onMatch }:
  { odds: OddsData; onMatch: (f: Fixture) => void }) {
  const groups = [..."ABCDEFGHIJKL"];
  return (
    <div>
      <p className="mb-4 text-sm text-muted">
        Live FIFA-format tables — played results are real, the <span className="text-fg">Adv</span> column
        is the model's chance of reaching the round of 32 (top two qualify directly,
        <span className="text-gold"> third place</span> can advance among the eight best thirds).
        Click a fixture in the Schedule tab for full match detail.
      </p>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {groups.map((g) => {
          const rows = standings(odds, g);
          const groupFixtures = odds.fixtures.filter((f) => f.group === g);
          return (
            <MagicCard key={g} className="rounded-2xl" gradientColor="#1a2540" gradientOpacity={0.6}>
              <div className="p-4">
                <h3 className="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-gold">
                  Group {g}
                </h3>
                <table className="w-full text-sm tabular-nums">
                  <thead>
                    <tr className="text-[11px] uppercase text-muted/80">
                      <th className="pb-1 text-left font-medium">Team</th>
                      <th className="w-7 font-medium">P</th>
                      <th className="w-7 font-medium">W</th>
                      <th className="w-7 font-medium">D</th>
                      <th className="w-7 font-medium">L</th>
                      <th className="w-9 font-medium">GD</th>
                      <th className="w-9 font-medium">Pts</th>
                      <th className="w-12 text-right font-medium">Adv</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={r.team} className={`border-t border-card2 ${posStyle(i)}`}>
                        <td className="max-w-0 truncate py-1.5 pl-2 pr-1">
                          <Flag team={r.team} /> {disp(r.team)}
                        </td>
                        <td className="text-center text-muted">{r.p}</td>
                        <td className="text-center text-muted">{r.w}</td>
                        <td className="text-center text-muted">{r.d}</td>
                        <td className="text-center text-muted">{r.l}</td>
                        <td className="text-center text-muted">{r.gf - r.ga > 0 ? "+" : ""}{r.gf - r.ga}</td>
                        <td className="text-center font-bold">{r.pts}</td>
                        <td className="text-right text-muted">{pct(r.advance)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {groupFixtures.map((f) => (
                    <button key={`${f.home}${f.away}`} onClick={() => onMatch(f)}
                      className="rounded-md border border-line bg-card2 px-2 py-1 text-[11px] text-muted transition-colors hover:border-pitch hover:text-fg"
                      title={`${disp(f.home)} vs ${disp(f.away)} · ${f.date}`}>
                      <Flag team={f.home} size={16} />{f.played ? ` ${f.home_score}-${f.away_score} ` : " – "}<Flag team={f.away} size={16} />
                    </button>
                  ))}
                </div>
              </div>
            </MagicCard>
          );
        })}
      </div>
    </div>
  );
}
