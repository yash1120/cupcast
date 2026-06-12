import { useEffect, useRef } from "react";
import { Chart } from "chart.js/auto";

import { BorderBeam } from "@/components/magicui/border-beam";
import { disp, flag } from "@/lib/flags";
import type { OddsData } from "@/lib/types";

export function OddsChart({ odds }: { odds: OddsData }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const rows = Object.entries(odds.teams)
      .map(([t, s]) => ({ t, champ: s.champion, final: s.final }))
      .sort((a, b) => b.champ - a.champ)
      .slice(0, 15);
    const chart = new Chart(canvasRef.current, {
      type: "bar",
      data: {
        labels: rows.map((r) => `${flag(r.t)} ${disp(r.t)}`),
        datasets: [
          { label: "Champion", data: rows.map((r) => +(r.champ * 100).toFixed(2)),
            backgroundColor: "#22d37f", borderRadius: 4 },
          { label: "Reach final", data: rows.map((r) => +(r.final * 100).toFixed(2)),
            backgroundColor: "#f5c54255", borderRadius: 4 },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: "#8a94ab", callback: (v) => v + "%" }, grid: { color: "#1f2940" } },
          y: { ticks: { color: "#e7ecf5", font: { size: 13 } }, grid: { display: false } },
        },
        plugins: {
          legend: { labels: { color: "#8a94ab" } },
          tooltip: { callbacks: { label: (c) => ` ${c.dataset.label}: ${c.parsed.x}%` } },
        },
      },
    });
    return () => chart.destroy();
  }, [odds]);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-line bg-card p-5">
      <div className="h-[460px]">
        <canvas ref={canvasRef} />
      </div>
      <BorderBeam size={120} duration={9} colorFrom="#22d37f" colorTo="#f5c542" />
    </div>
  );
}
