import type { H2H, MatchDetail, Metrics, OddsData, Player, TeamInfo, WeatherMap } from "./types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

const q = encodeURIComponent;

export const getOdds = () => get<OddsData>("/api/odds");
export const getMetrics = () => get<Metrics>("/api/metrics");
export const getTeams = () => get<{ teams: TeamInfo[] }>("/api/teams");
export const getWeather = () =>
  get<{ fetched_on: string; forecasts: WeatherMap }>("/api/weather");
export const getDetail = (home: string, away: string, neutral: boolean) =>
  get<MatchDetail>(`/api/detail?home=${q(home)}&away=${q(away)}&neutral=${neutral}`);
export const getH2H = (a: string, b: string) => get<H2H>(`/api/h2h?a=${q(a)}&b=${q(b)}`);
export const getSquad = (team: string) =>
  get<{ team: string; players: Player[] }>(`/api/squads?team=${q(team)}`);
