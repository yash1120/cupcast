import { useState } from "react";

import { ShimmerButton } from "@/components/magicui/shimmer-button";
import { Flag, MarketList, ProbBar, ProbLabels, ScoreList, SectionTitle } from "@/components/shared";
import { getDetail } from "@/lib/api";
import { disp, flag } from "@/lib/flags";
import type { MatchDetail, TeamInfo } from "@/lib/types";

const selectCls =
  "min-w-52 rounded-lg border border-line bg-card2 px-3 py-2.5 text-sm text-fg outline-none focus:border-pitch";

export function H2HPicker({ teams }: { teams: TeamInfo[] }) {
  const [home, setHome] = useState("Australia");
  const [away, setAway] = useState("United States");
  const [neutral, setNeutral] = useState(true);
  const [detail, setDetail] = useState<MatchDetail | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    if (home === away || busy) return;
    setBusy(true);
    try {
      setDetail(await getDetail(home, away, neutral));
    } finally {
      setBusy(false);
    }
  }

  const options = teams.map((t) => (
    <option key={t.name} value={t.name}>
      {flag(t.name)} {disp(t.name)} ({t.elo})
    </option>
  ));

  return (
    <div className="rounded-2xl border border-line bg-card p-5">
      <div className="flex flex-wrap items-center gap-3">
        <select className={selectCls} value={home} onChange={(e) => setHome(e.target.value)}>
          {options}
        </select>
        <span className="text-sm text-muted">vs</span>
        <select className={selectCls} value={away} onChange={(e) => setAway(e.target.value)}>
          {options}
        </select>
        <label className="flex items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={neutral} onChange={(e) => setNeutral(e.target.checked)} />
          neutral venue
        </label>
        <ShimmerButton onClick={run} background="#102218" shimmerColor="#22d37f"
          className="px-6 py-2.5 text-sm font-bold text-pitch">
          {busy ? "Predicting…" : "Predict"}
        </ShimmerButton>
      </div>

      {detail && (
        <div className="mt-5">
          <div className="mb-2 flex justify-between text-[15px] font-bold">
            <span><Flag team={home} /> {disp(home)} <span className="text-xs font-normal text-muted">Elo {detail.elo_home}</span></span>
            <span><span className="text-xs font-normal text-muted">Elo {detail.elo_away}</span> {disp(away)} <Flag team={away} /></span>
          </div>
          <ProbBar pHome={detail.p_home} pDraw={detail.p_draw} pAway={detail.p_away} />
          <ProbLabels pHome={detail.p_home} pDraw={detail.p_draw} pAway={detail.p_away} />
          <p className="mt-2 text-xs text-muted">
            Expected goals {detail.exp_goals_home.toFixed(2)} – {detail.exp_goals_away.toFixed(2)}
            {neutral ? " (neutral venue)" : " (home advantage applied)"}
          </p>
          <div className="mt-4 grid gap-6 md:grid-cols-2">
            <div>
              <SectionTitle>Most likely scorelines</SectionTitle>
              <ScoreList scorelines={detail.top_scorelines} />
            </div>
            <div>
              <SectionTitle>Markets</SectionTitle>
              <MarketList markets={detail.markets} home={home} away={away} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
