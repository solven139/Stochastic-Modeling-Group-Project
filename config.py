"""Project-wide conventions. Every module reads these, so all numbers agree."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"          # data/RTH, data/ETH, data/events.csv (prof's files, not in git)
OUT = ROOT / "out"            # every generated file

RATE = 0.043                  # 3-month T-bill, April 2025; discount factor D = exp(-RATE * T)
STRIKE_STEP = 25.0            # strike spacing in the option tables
LOWEST_STRIKE = 4600.0        # data limit: nothing quoted below this

# The five phase snapshots used in every chart (ET)
PHASES = {
    "1 Before":      pd.Timestamp("2025-04-01 15:55"),
    "2 Shock":       pd.Timestamp("2025-04-03 10:00"),
    "3 Retaliation": pd.Timestamp("2025-04-04 15:55"),
    "4 Escalation":  pd.Timestamp("2025-04-08 15:55"),
    "5 Pause":       pd.Timestamp("2025-04-09 15:55"),
}

# Verified event onsets (ET) for the fake vs real comparison; see events_verified.csv
FAKE_PAUSE = pd.Timestamp("2025-04-07 10:10")   # Part A verified time
REAL_PAUSE = pd.Timestamp("2025-04-09 13:18")
