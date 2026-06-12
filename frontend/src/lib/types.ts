export interface TeamOdds {
  group: string;
  elo: number;
  exp_points: number;
  win_group: number;
  advance: number;
  r32: number;
  r16: number;
  qf: number;
  sf: number;
  final: number;
  champion: number;
}

export interface Fixture {
  date: string;
  home: string;
  away: string;
  city: string;
  stadium: string;
  neutral: boolean;
  group: string;
  played: boolean;
  home_score: number | null;
  away_score: number | null;
  p_home?: number;
  p_draw?: number;
  p_away?: number;
  xg_home?: number;
  xg_away?: number;
}

export interface BracketTie {
  match: number;
  a: string;
  b: string;
  p_a: number;
  winner: string;
}

export interface OddsData {
  generated_at: string;
  n_sims: number;
  results_through: string;
  teams: Record<string, TeamOdds>;
  fixtures: Fixture[];
  top_finals: { pair: string[]; p: number }[];
  bracket: Record<"r32" | "r16" | "qf" | "sf" | "final", BracketTie[]>;
}

export interface Metrics {
  trained_at: string;
  training_samples: number;
  test_window: string;
  model: { accuracy: number; log_loss: number; brier: number };
  elo_baseline: { accuracy: number; log_loss: number; brier: number };
  majority_class_accuracy: number;
}

export interface TeamInfo {
  name: string;
  display: string;
  group: string;
  host: boolean;
  elo: number;
}

export interface MatchDetail {
  home: string;
  away: string;
  neutral: boolean;
  p_home: number;
  p_draw: number;
  p_away: number;
  exp_goals_home: number;
  exp_goals_away: number;
  elo_home: number;
  elo_away: number;
  top_scorelines: { score: string; p: number }[];
  markets: {
    over_1_5: number;
    over_2_5: number;
    over_3_5: number;
    btts: number;
    clean_sheet_home: number;
    clean_sheet_away: number;
    win_to_nil_home: number;
    win_to_nil_away: number;
  };
}

export interface H2H {
  a: string;
  b: string;
  matches: number;
  a_wins: number;
  b_wins: number;
  draws: number;
  a_goals: number;
  b_goals: number;
  recent: { date: string; home: string; away: string; score: string; tournament: string }[];
}

export interface Player {
  no: number | null;
  pos: string;
  name: string;
  age: number | null;
  caps: number;
  goals: number;
  club: string;
}

export interface WeatherDay {
  stadium: string;
  tmax_c: number;
  tmin_c: number;
  precip_prob: number;
  wind_kmh: number;
  elevation_m: number;
}

export type WeatherMap = Record<string, WeatherDay>;
