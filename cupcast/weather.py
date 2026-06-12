"""Match-day weather forecasts from Open-Meteo (free, no API key).

Forecasts are *display context* for upcoming fixtures — the outcome model was
never trained on historical weather, so they are deliberately not model inputs.

Run:  python -m cupcast.weather
"""
import json
import urllib.parse
import urllib.request
from datetime import date, timedelta

from . import config
from .features import load_results

# The 16 official venues: dataset city -> (lat, lon, stadium label)
VENUES = {
    "Arlington":       (32.7473, -97.0945, "AT&T Stadium, Dallas"),
    "Atlanta":         (33.7554, -84.4009, "Mercedes-Benz Stadium, Atlanta"),
    "East Rutherford": (40.8128, -74.0742, "MetLife Stadium, New York/NJ"),
    "Foxborough":      (42.0909, -71.2643, "Gillette Stadium, Boston"),
    "Guadalupe":       (25.6695, -100.2441, "Estadio BBVA, Monterrey"),
    "Houston":         (29.6847, -95.4107, "NRG Stadium, Houston"),
    "Inglewood":       (33.9535, -118.3392, "SoFi Stadium, Los Angeles"),
    "Kansas City":     (39.0489, -94.4839, "Arrowhead Stadium, Kansas City"),
    "Mexico City":     (19.3029, -99.1505, "Estadio Azteca, Mexico City"),
    "Miami Gardens":   (25.9580, -80.2389, "Hard Rock Stadium, Miami"),
    "Philadelphia":    (39.9008, -75.1675, "Lincoln Financial Field, Philadelphia"),
    "Santa Clara":     (37.4033, -121.9694, "Levi's Stadium, San Francisco Bay"),
    "Seattle":         (47.5952, -122.3316, "Lumen Field, Seattle"),
    "Toronto":         (43.6332, -79.4186, "BMO Field, Toronto"),
    "Vancouver":       (49.2768, -123.1120, "BC Place, Vancouver"),
    "Zapopan":         (20.6817, -103.4625, "Estadio Akron, Guadalajara"),
}
FORECAST_HORIZON_DAYS = 15
API = "https://api.open-meteo.com/v1/forecast"


def _fetch_venue(lat, lon, start, end):
    params = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,"
                 "precipitation_probability_max,wind_speed_10m_max",
        "timezone": "auto", "start_date": start, "end_date": end,
    })
    with urllib.request.urlopen(f"{API}?{params}", timeout=30) as resp:
        return json.loads(resp.read())


def build(out_path=None):
    df = load_results()
    wc = df[(df.tournament == "FIFA World Cup") & (df.date >= config.WC_START)
            & df.home_score.isna()]
    today = date.today()
    horizon = today + timedelta(days=FORECAST_HORIZON_DAYS)

    # group needed dates per venue so it's one API call per stadium
    needed = {}
    for r in wc.itertuples(index=False):
        d = r.date.date()
        if r.city in VENUES and today <= d <= horizon:
            needed.setdefault(r.city, set()).add(str(d))

    out = {}
    for city, dates in sorted(needed.items()):
        lat, lon, label = VENUES[city]
        data = _fetch_venue(lat, lon, min(dates), max(dates))
        daily = data["daily"]
        for i, d in enumerate(daily["time"]):
            if d not in dates:
                continue
            out[f"{d}|{city}"] = {
                "stadium": label,
                "tmax_c": daily["temperature_2m_max"][i],
                "tmin_c": daily["temperature_2m_min"][i],
                "precip_prob": daily["precipitation_probability_max"][i],
                "wind_kmh": daily["wind_speed_10m_max"][i],
                "elevation_m": round(data.get("elevation", 0)),
            }
        print(f"  {city:<16} {len([d for d in daily['time'] if d in dates])} match day(s)")

    path = out_path or config.MODELS_DIR / "weather.json"
    path.write_text(json.dumps({"fetched_on": str(today), "forecasts": out}, indent=1))
    print(f"Saved {len(out)} fixture forecasts -> {path}")
    return out


if __name__ == "__main__":
    build()
