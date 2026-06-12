"""Download / refresh the results dataset (no API key required).

Run:  python scripts/download_data.py
Re-run any time — newly played World Cup matches get locked into the
simulation on the next train + simulate.
"""
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cupcast import config  # noqa: E402

config.DATA_DIR.mkdir(exist_ok=True)
print(f"Downloading {config.DATA_URL} ...")
urllib.request.urlretrieve(config.DATA_URL, config.RESULTS_CSV)
size = config.RESULTS_CSV.stat().st_size
print(f"Saved {config.RESULTS_CSV} ({size / 1e6:.1f} MB)")
