import { Flag } from "@/components/shared";
import { disp, pct } from "@/lib/flags";
import type { BracketTie, OddsData } from "@/lib/types";

const ROUNDS: { key: keyof OddsData["bracket"]; label: string }[] = [
  { key: "r32", label: "Round of 32" },
  { key: "r16", label: "Round of 16" },
  { key: "qf", label: "Quarter-finals" },
  { key: "sf", label: "Semi-finals" },
  { key: "final", label: "Final" },
];

function TieCard({ tie }: { tie: BracketTie }) {
  const row = (team: string, p: number) => (
    <div className={`flex items-center justify-between gap-2 px-3 py-1.5 text-[13px] ${
      tie.winner === team ? "font-bold text-fg" : "text-muted"}`}>
      <span className="truncate"><Flag team={team} size={16} /> {disp(team)}</span>
      <span className="shrink-0 tabular-nums text-[11px]">{pct(p)}</span>
    </div>
  );
  return (
    <div className="w-52 shrink-0 divide-y divide-card2 rounded-lg border border-line bg-card">
      {row(tie.a, tie.p_a)}
      {row(tie.b, 1 - tie.p_a)}
    </div>
  );
}

export function BracketView({ odds }: { odds: OddsData }) {
  const champion = odds.bracket.final[0]?.winner;
  return (
    <div>
      <p className="mb-4 text-sm text-muted">
        Projected knockout bracket on the official FIFA match plan (matches 73–104) —
        every slot filled with the most likely qualifier, every tie resolved to the
        higher win-probability side (percentages include extra-time/penalty chances).
        One plausible path of {odds.n_sims.toLocaleString()} simulated — upsets guaranteed.
      </p>
      <div className="overflow-x-auto pb-4">
        <div className="flex min-w-max gap-6">
          {ROUNDS.map(({ key, label }) => (
            <div key={key} className="flex flex-col">
              <h3 className="mb-3 text-center text-[11px] font-bold uppercase tracking-[0.2em] text-gold">
                {label}
              </h3>
              <div className="flex grow flex-col justify-around gap-2">
                {odds.bracket[key].map((tie) => <TieCard key={tie.match} tie={tie} />)}
              </div>
            </div>
          ))}
          {champion && (
            <div className="flex flex-col">
              <h3 className="mb-3 text-center text-[11px] font-bold uppercase tracking-[0.2em] text-gold">
                Champion
              </h3>
              <div className="flex grow flex-col justify-around">
                <div className="w-52 rounded-xl border border-gold/50 bg-gradient-to-br from-card to-card2 px-4 py-5 text-center">
                  <div className="text-3xl">🏆</div>
                  <div className="mt-1 font-bold"><Flag team={champion} /> {disp(champion)}</div>
                  <div className="mt-1 text-xs text-muted">
                    title odds {pct(odds.teams[champion]?.champion ?? 0)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
