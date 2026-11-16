"""Step 5: the Q side. Fit the model ladder to every 15-minute smile and around both pauses.

Outputs (out/):
  q_shared.json          shared parameters from the pooled stage, per model
  q_fits_15m.parquet     every model, every 15 minutes in regular hours
  q_fits_events.parquet  every model, every 3 minutes from -30 to +60 minutes around both pauses
  girsanov_test.csv      Bates v0 (Q) vs realized bipower variance (P) at each 15-minute snapshot
"""
import json
import time

import pandas as pd

from libday.config import FAKE_PAUSE, OUT, REAL_PAUSE
from libday.qfit import (SPECS, fit_black_scholes, fit_sabr_series, fit_series, fit_shared,
                         p_anchor, snapshot_dict)

t0 = time.time()
ivs = pd.read_parquet(OUT / "ivs.parquet")
by_time = dict(tuple(ivs[ivs.session == "RTH"].groupby("time")))
times = sorted(by_time)

grid_15m = [t for t in times if t.minute % 15 == 0]
pool = [t for t in times if t.strftime("%H:%M") in ("10:30", "12:30", "15:30")]
events = sorted({t for e in (FAKE_PAUSE, REAL_PAUSE) for t in times
                 if pd.Timedelta("-30min") <= t - e <= pd.Timedelta("60min") and t.minute % 3 == 0})
snaps = {t: snapshot_dict(by_time[t]) for t in sorted(set(grid_15m) | set(pool) | set(events))}
print(f"{len(grid_15m)} snapshots every 15 min, {len(pool)} pooled, {len(events)} around the pauses")

# Stage 1: shared parameters from the pooled subset
shared, report = {}, {}
for name in SPECS:
    s, res = fit_shared(name, [snaps[t] for t in pool])
    shared[name] = s
    report[name] = {"shared": dict(zip(SPECS[name].shared_names, map(float, s))),
                    "pooled_rmse_vp": float(res.rmse_vol_all * 100), "success": res.success}
    print(f"stage 1 {name:7s} {report[name]['shared']}  pooled rmse {report[name]['pooled_rmse_vp']:.2f} vp "
          f"({time.time() - t0:.0f}s)")
json.dump(report, open(OUT / "q_shared.json", "w"), indent=2)

# Stage 2: every snapshot, shared parameters fixed
def run(ts):
    ss = [snaps[t] for t in ts]
    parts = [fit_black_scholes(ss), fit_sabr_series(ss)] + [fit_series(n, shared[n], ss) for n in SPECS]
    return pd.concat(parts, ignore_index=True)

fits = run(grid_15m)
fits.to_parquet(OUT / "q_fits_15m.parquet")
print(f"stage 2: 15-minute fits done ({time.time() - t0:.0f}s)")
run(events).to_parquet(OUT / "q_fits_events.parquet")
print(f"stage 2: event-window fits done ({time.time() - t0:.0f}s)")

# Fit quality by day and model (vol points)
print((fits.pivot_table(index=fits.time.dt.date, columns="model", values="rmse_vp", aggfunc="median")
       .round(2).to_string()))

# Girsanov test: diffusion variance under Q (Bates v0) vs P (realized bipower)
es = pd.read_parquet(OUT / "es_3s.parquet").ES
g = p_anchor(es, grid_15m).merge(fits[fits.model == "bates"][["time", "v0", "lam"]], on="time")
g["vol_q"], g["vol_p"] = g.v0 ** 0.5 * 100, g.v0_p ** 0.5 * 100
g.to_csv(OUT / "girsanov_test.csv", index=False)
d = g[g.full_coverage].groupby(g.time.dt.date)[["vol_q", "vol_p", "lam"]].median().round(2)
print("Girsanov test (daily medians, full-coverage windows only):\n" + d.to_string())
