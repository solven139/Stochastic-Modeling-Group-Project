"""Step 7: fake vs real pause. Event paths, credibility and persistence ratios, densities, leak test.

Outputs (out/): event_paths.csv, event_ratios.csv, event_densities.parquet, leak_test.csv
"""
import pandas as pd

from libday.config import DATA, FAKE_PAUSE, OUT, REAL_PAUSE
from libday.density import density
from libday.events import event_path, leak_rank, quiet_windows, ratios

es = pd.read_parquet(OUT / "es_1min.parquet").ES
kp = pd.read_parquet(OUT / "keypoints.parquet")
kp = kp[kp.session == "RTH"]
q = pd.read_parquet(OUT / "q_fits_events.parquet")
bates = q[q.model == "bates"].set_index("time")
sabr = q[q.model == "sabr"].set_index("time")

measures = {
    "es": es,
    "atm": kp["atm"], "put95": kp["put95"], "skew": kp["skew"],
    "bates_vol": bates.v0 ** 0.5 * 100, "bates_lam": bates.lam,
    "sabr_rho": sabr.rho, "sabr_nu": sabr.nu,
}
names = [k for k in measures if k != "es"]

paths, rat = [], []
for label, onset in [("fake", FAKE_PAUSE), ("real", REAL_PAUSE)]:
    p = event_path(measures, onset)
    p["event"] = label
    paths.append(p.reset_index())
    r = ratios(p, names)
    r["event"] = label
    rat.append(r.reset_index())
paths, rat = pd.concat(paths), pd.concat(rat)
paths.to_csv(OUT / "event_paths.csv", index=False)
rat.to_csv(OUT / "event_ratios.csv", index=False)
print("Change from -5 min, then credibility (per 1% rally at +10) and persistence (+60 / +10):")
print(rat.pivot(index="measure", columns="event",
                values=["change_+10", "change_+60", "per_1pct_rally", "persistence"]).round(2).to_string())

# Risk-neutral densities at -5, +10, +60 minutes around each pause
ivs = pd.read_parquet(OUT / "ivs.parquet")
by_time = dict(tuple(ivs[ivs.session == "RTH"].groupby("time")))
dens, rows = [], []
for label, onset in [("fake", FAKE_PAUSE), ("real", REAL_PAUSE)]:
    for tau in (-5, 10, 60):
        t = max(x for x in by_time if x <= onset + pd.Timedelta(minutes=tau))
        d, s = density(by_time[t])
        d["event"], d["tau"] = label, tau
        dens.append(d)
        rows.append({"event": label, "tau": tau, "p_down10": s["p_down10"], "q10": s["q10"],
                     "kelly_skew": s["kelly_skew"], "sd": s["sd"]})
pd.concat(dens).to_parquet(OUT / "event_densities.parquet")
print("\nRisk-neutral distribution around each pause:")
print(pd.DataFrame(rows).pivot(index="tau", columns="event").round(3).to_string())

# Leak test: the 30 minutes before each onset against quiet windows
ev = pd.read_csv(DATA / "events_verified_A.csv", parse_dates=["listed_time", "source_time", "verified_time"])
jumps = pd.read_csv(OUT / "jumps_flagged.csv", parse_dates=[0]).iloc[:, 0]
news = pd.concat([ev.listed_time, ev.source_time.dropna(), ev.verified_time.dropna(), jumps, pd.Series([FAKE_PAUSE, REAL_PAUSE])])
quiet = quiet_windows(kp.index, news)
leak = []
for label, onset in [("fake", FAKE_PAUSE), ("real", REAL_PAUSE)]:
    for name, s, pct in [("futures %", es, True), ("ATM vol", kp["atm"], False), ("5% put vol", kp["put95"], False)]:
        leak.append({"event": label, "measure": name, **leak_rank(s, onset, quiet, pct=pct)})
leak = pd.DataFrame(leak)
leak.to_csv(OUT / "leak_test.csv", index=False)
print(f"\nLeak test: 30 minutes before onset vs {len(quiet)} quiet windows (rank 0.95+ = top 5%):")
print(leak.round(3).to_string(index=False))
