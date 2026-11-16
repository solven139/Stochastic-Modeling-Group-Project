"""Part E summary tables for the report: model ladder, Bates by phase, Girsanov test, fear premium,
fake vs real, leak test (raw and volatility-scaled). Writes out/part_e/*.csv and prints them."""
import json
import numpy as np
import pandas as pd
from libday.config import FAKE_PAUSE, OUT, PHASES, REAL_PAUSE

E = OUT / "part_e"; E.mkdir(exist_ok=True)
fits = pd.read_parquet(OUT / "q_fits_15m.parquet")

# 1. Model ladder: median fit error (vol points) by day
ladder = fits.pivot_table(index=fits.time.dt.date, columns="model", values="rmse_vp", aggfunc="median")
ladder = ladder[["black_scholes", "merton", "heston", "sabr", "bates"]].round(2)
ladder.to_csv(E / "e1_model_ladder.csv"); print("E1 model ladder (median RMSE, vol pts)\n", ladder.to_string(), "\n")
print("shared:", json.dumps({k: v["shared"] for k, v in json.load(open(OUT / "q_shared.json")).items()}, indent=None), "\n")

# 2. Bates at the five phases
b = fits[fits.model == "bates"].set_index("time")
near = {n: b.index[b.index.get_indexer([t], method="nearest")[0]] for n, t in PHASES.items()}
ph = pd.DataFrame({f"{n} ({near[n]:%d %b %H:%M})": b.loc[near[n], ["v0", "rho", "gamma", "lam", "rmse_vp"]] for n in PHASES}).T
ph["diffusion_vol_%"] = np.sqrt(ph.v0.astype(float)) * 100
ph = ph[["diffusion_vol_%", "rho", "gamma", "lam", "rmse_vp"]].astype(float).round(3)
ph.to_csv(E / "e2_bates_phases.csv"); print("E2 Bates at the phases\n", ph.to_string(), "\n")

# 3. Girsanov test, daily medians
g = pd.read_csv(OUT / "girsanov_test.csv", parse_dates=["time"])
gd = g[g.full_coverage].groupby(g.time.dt.date)[["vol_q", "vol_p"]].median().round(1)
gd["gap"] = (gd.vol_q - gd.vol_p).round(1)
gd.to_csv(E / "e3_girsanov.csv"); print("E3 Girsanov test: Q (Bates diffusion) vs P (bipower, trailing)\n", gd.to_string(), "\n")

# 4. Fear premium, daily medians
p = pd.read_csv(OUT / "premiums.csv", parse_dates=["time"])
cols = ["q_diff", "p_diff", "q_jump", "p_jump", "q_total", "p_total", "premium_diff", "premium_jump", "premium_total"]
pd_ = p.groupby(p.time.dt.date)[cols].median().round(1)
pd_.to_csv(E / "e4_premium.csv"); print("E4 fear premium (vol pts, next trading day)\n", pd_.to_string(), "\n")

# 5. Fake vs real: only measures whose ratios are meaningful
r = pd.read_csv(OUT / "event_ratios.csv")
r = r[r.measure.isin(["atm", "put95", "skew", "bates_vol"])].round(2)
r.to_csv(E / "e5_fake_vs_real.csv", index=False); print("E5 fake vs real\n", r.to_string(index=False), "\n")

# 6. Leak test: raw (from step 7) plus a volatility-scaled version and the 13:02 one-minute jump
es = pd.read_parquet(OUT / "es_1min.parquet").ES
rows, z_all = [], []
for d in sorted({t.date() for t in es.index}):
    s = es[str(d)].between_time("09:31", "16:00")
    if len(s) < 100:
        continue
    sd = np.log(s).diff().std() * np.sqrt(30)
    for st in pd.date_range(f"{d} 09:45", f"{d} 15:30", freq="15min"):
        z_all.append(np.log(s.asof(st + pd.Timedelta("30min")) / s.asof(st)) / sd)
z_all = np.abs(np.array(z_all))
for label, on in [("fake", FAKE_PAUSE), ("real", REAL_PAUSE)]:
    s = es[str(on.date())].between_time("09:31", "16:00")
    sd = np.log(s).diff().std() * np.sqrt(30)
    z = np.log(s.asof(on) / s.asof(on - pd.Timedelta("30min"))) / sd
    rows.append({"event": label, "pre30_move_%": round((s.asof(on) / s.asof(on - pd.Timedelta("30min")) - 1) * 100, 2),
                 "z_vs_day_vol": round(z, 2), "rank_vol_scaled": round((z_all < abs(z)).mean(), 3), "n_windows": len(z_all)})
leak = pd.read_csv(OUT / "leak_test.csv")
pd.DataFrame(rows).to_csv(E / "e6_leak_volscaled.csv", index=False)
leak.round(3).to_csv(E / "e6_leak_raw.csv", index=False)
print("E6 leak test, raw ranks vs quiet windows\n", leak.round(3).to_string(index=False))
print("E6 leak test, volatility-scaled\n", pd.DataFrame(rows).to_string(index=False))
r1 = np.log(es).diff().mul(1e4)
r1 = r1[r1.index.to_series().diff() <= pd.Timedelta("1min")]
rth = r1[(r1.index.time >= pd.Timestamp("09:31").time()) & (r1.index.time <= pd.Timestamp("16:00").time())]
v = rth.loc["2025-04-09 13:02"]
print(f"\n13:02 on Apr 9: {v:+.0f} bp; larger than {(rth.abs() < abs(v)).mean():.1%} of the week's 1-min moves; "
      f"{(rth.abs() >= abs(v)).sum()} moves that size all week; Apr 9 pre-pause 1-min sd "
      f"{rth.loc['2025-04-09 09:45':'2025-04-09 13:00'].std():.1f} bp")
