"""Step 6: the fear premium, Q minus P, for the diffusive (volatility) part and the jump (crash) part."""
import pandas as pd

from libday.config import OUT
from libday.premiums import premium_table
from libday.realized import returns

es = pd.read_parquet(OUT / "es_3s.parquet").ES
r, gaps = returns(es, "5min")
fits = pd.read_parquet(OUT / "q_fits_15m.parquet")
table = premium_table(fits[fits.model == "bates"], r, gaps)
table.to_csv(OUT / "premiums.csv", index=False)

cols = ["q_diff", "p_diff", "q_jump", "p_jump", "q_total", "p_total",
        "premium_diff", "premium_jump", "premium_total"]
print("Daily medians, annualised vol %, next trading day (premium = Q - P, vol points):")
print(table.groupby(table.time.dt.date)[cols].median().round(1).to_string())
