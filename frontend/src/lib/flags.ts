const ISO: Record<string, string> = {
  Mexico: "MX", "South Africa": "ZA", "South Korea": "KR", "Czech Republic": "CZ",
  Canada: "CA", "Bosnia and Herzegovina": "BA", Qatar: "QA", Switzerland: "CH",
  Brazil: "BR", Morocco: "MA", Haiti: "HT", "United States": "US", Paraguay: "PY",
  Australia: "AU", Turkey: "TR", Germany: "DE", "Curaçao": "CW", "Ivory Coast": "CI",
  Ecuador: "EC", Netherlands: "NL", Japan: "JP", Sweden: "SE", Tunisia: "TN",
  Belgium: "BE", Egypt: "EG", Iran: "IR", "New Zealand": "NZ", Spain: "ES",
  "Cape Verde": "CV", "Saudi Arabia": "SA", Uruguay: "UY", France: "FR",
  Senegal: "SN", Iraq: "IQ", Norway: "NO", Argentina: "AR", Algeria: "DZ",
  Austria: "AT", Jordan: "JO", Portugal: "PT", "DR Congo": "CD", Uzbekistan: "UZ",
  Colombia: "CO", Croatia: "HR", Ghana: "GH", Panama: "PA",
};

const SPECIAL: Record<string, string> = {
  England: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  Scotland: "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
};

const DISPLAY: Record<string, string> = {
  "Czech Republic": "Czechia",
  Turkey: "Türkiye",
  "Cape Verde": "Cabo Verde",
};

export const flag = (team: string): string =>
  SPECIAL[team] ??
  (ISO[team]
    ? [...ISO[team]].map((c) => String.fromCodePoint(127397 + c.charCodeAt(0))).join("")
    : "🏳️");

/** flagcdn.com code — Windows lacks emoji flags, so we render images instead. */
export const flagCode = (team: string): string | null => {
  if (team === "England") return "gb-eng";
  if (team === "Scotland") return "gb-sct";
  return ISO[team]?.toLowerCase() ?? null;
};

export const disp = (team: string): string => DISPLAY[team] ?? team;

export const pct = (x: number): string => (x * 100).toFixed(x >= 0.095 ? 0 : 1) + "%";

export const fmtDate = (iso: string): string =>
  new Date(iso + "T12:00:00").toLocaleDateString("en-AU", {
    weekday: "long", day: "numeric", month: "long",
  });
