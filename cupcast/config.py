"""Central configuration: paths, tournament structure, model constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
WEB_DIR = ROOT / "web"
RESULTS_CSV = DATA_DIR / "results.csv"
DATA_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"

# ---------------------------------------------------------------- Elo engine
ELO_START = 1500.0
ELO_HOME_ADV = 80.0  # rating bonus for a true (non-neutral) home side
# K-factor by match importance, keyed on substrings of the tournament column.
K_FACTORS = [
    ("FIFA World Cup qualification", 40.0),
    ("FIFA World Cup", 60.0),
    ("Copa América", 50.0),
    ("UEFA Euro qualification", 40.0),
    ("UEFA Euro", 50.0),
    ("African Cup of Nations qualification", 40.0),
    ("African Cup of Nations", 50.0),
    ("AFC Asian Cup qualification", 40.0),
    ("AFC Asian Cup", 50.0),
    ("CONCACAF Championship", 50.0),
    ("Gold Cup", 50.0),
    ("Confederations Cup", 50.0),
    ("UEFA Nations League", 40.0),
    ("CONCACAF Nations League", 40.0),
    ("qualification", 40.0),
    ("Friendly", 20.0),
]
K_DEFAULT = 30.0

# ------------------------------------------------------------------ training
TRAIN_START = "1990-01-01"   # modern era only
TEST_SPLIT = "2024-01-01"    # everything from here is the hold-out set
MIN_PRIOR_MATCHES = 30       # both teams need this much history to be a sample
FORM_WINDOW = 8              # matches used for rolling form features

# ------------------------------------------------------- World Cup 2026 draw
# Names exactly as they appear in the dataset.
GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}
WC_TEAMS = [t for g in GROUPS.values() for t in g]
TEAM_GROUP = {t: g for g, teams in GROUPS.items() for t in teams}
HOSTS = {"United States", "Mexico", "Canada"}
WC_START = "2026-06-11"

# Dataset name -> preferred display name (UI only).
DISPLAY_NAMES = {"Czech Republic": "Czechia", "Turkey": "Türkiye", "Cape Verde": "Cabo Verde"}

# ------------------------------------------------- official knockout bracket
# Round of 32 (match number -> (slot, slot)). "1A" = winner of group A,
# "2A" = runner-up, "3:ABCDF" = a best-third drawn from that pool of groups.
R32 = {
    73: ("2A", "2B"), 74: ("1E", "3:ABCDF"), 75: ("1F", "2C"), 76: ("1C", "2F"),
    77: ("1I", "3:CDFGH"), 78: ("2E", "2I"), 79: ("1A", "3:CEFHI"), 80: ("1L", "3:EHIJK"),
    81: ("1D", "3:BEFIJ"), 82: ("1G", "3:AEHIJ"), 83: ("2K", "2L"), 84: ("1H", "2J"),
    85: ("1B", "3:EFGIJ"), 86: ("1J", "2H"), 87: ("1K", "3:DEIJL"), 88: ("2D", "2G"),
}
R16 = {89: (74, 77), 90: (73, 75), 91: (76, 78), 92: (79, 80),
       93: (83, 84), 94: (81, 82), 95: (86, 88), 96: (85, 87)}
QF = {97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96)}
SF = {101: (97, 98), 102: (99, 100)}
FINAL = {104: (101, 102)}

N_SIMULATIONS = 5000
