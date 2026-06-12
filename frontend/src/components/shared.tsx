import { disp, flagCode, pct } from "@/lib/flags";
import type { MatchDetail } from "@/lib/types";

export function Flag({ team, size = 20 }: { team: string; size?: number }) {
  const code = flagCode(team);
  if (!code) return <span>🏳️</span>;
  // flagcdn only serves fixed widths (w20/w40/...); scale with the width attr
  return (
    <img src={`https://flagcdn.com/w20/${code}.png`}
      srcSet={`https://flagcdn.com/w40/${code}.png 2x`}
      width={size} alt={`${team} flag`} loading="lazy"
      className="inline-block rounded-[2px] align-[-2px]" />
  );
}

export function ProbBar({ pHome, pDraw, pAway, className = "" }:
  { pHome: number; pDraw: number; pAway: number; className?: string }) {
  return (
    <div className={`flex h-2 overflow-hidden rounded-full ${className}`}>
      <div className="bg-pitch" style={{ width: `${pHome * 100}%` }} />
      <div className="bg-[#3c465e]" style={{ width: `${pDraw * 100}%` }} />
      <div className="bg-loss" style={{ width: `${pAway * 100}%` }} />
    </div>
  );
}

export function ProbLabels({ pHome, pDraw, pAway }:
  { pHome: number; pDraw: number; pAway: number }) {
  return (
    <div className="mt-1.5 flex justify-between text-xs tabular-nums text-muted">
      <span className="text-pitch">{pct(pHome)}</span>
      <span>draw {pct(pDraw)}</span>
      <span className="text-loss">{pct(pAway)}</span>
    </div>
  );
}

export function ScoreList({ scorelines }: { scorelines: { score: string; p: number }[] }) {
  const max = scorelines[0]?.p ?? 1;
  return (
    <div>
      {scorelines.map((s) => (
        <div key={s.score} className="grid grid-cols-[44px_1fr_48px] items-center gap-2 border-t border-card2 py-1.5 text-sm tabular-nums">
          <span className="font-semibold">{s.score}</span>
          <span className="h-1.5 overflow-hidden rounded-full bg-card2">
            <span className="block h-full rounded-full bg-gradient-to-r from-pitch to-gold"
              style={{ width: `${(s.p / max) * 100}%` }} />
          </span>
          <span className="text-right text-muted">{pct(s.p)}</span>
        </div>
      ))}
    </div>
  );
}

export function MarketList({ markets, home, away }:
  { markets: MatchDetail["markets"]; home: string; away: string }) {
  const rows: [string, number][] = [
    ["Over 1.5 goals", markets.over_1_5],
    ["Over 2.5 goals", markets.over_2_5],
    ["Over 3.5 goals", markets.over_3_5],
    ["Both teams score", markets.btts],
    [`${disp(home)} clean sheet`, markets.clean_sheet_home],
    [`${disp(away)} clean sheet`, markets.clean_sheet_away],
    [`${disp(home)} wins to nil`, markets.win_to_nil_home],
    [`${disp(away)} wins to nil`, markets.win_to_nil_away],
  ];
  return (
    <div>
      {rows.map(([label, p]) => (
        <div key={label} className="flex justify-between border-t border-card2 py-1.5 text-sm">
          <span>{label}</span>
          <span className="tabular-nums text-muted">{pct(p)}</span>
        </div>
      ))}
    </div>
  );
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="mb-2 text-xs font-semibold uppercase tracking-widest text-gold">
      {children}
    </h4>
  );
}

export function Disclaimer() {
  return (
    <p className="mt-4 text-center text-xs text-muted/70">
      Model estimates for entertainment — not betting advice.
    </p>
  );
}
