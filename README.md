# Stochastic-Modeling-Group-Project

# Liberation Day 2025: how the options market priced fear

QF620 Stochastic Modelling in Finance, group project, SMU MQF (2026-27 Term 1).

We study SPX options and ES futures over 1-10 April 2025, the week of the "Liberation Day"
tariffs. We ask how much the options market feared a crash, how that compares with what
the market then did, and how options reacted to a fake and a real "90-day pause" headline.

## Questions

1. How did SPX and its implied volatility behave? (Parts A, B, D)
2. How did the risk-neutral distribution of SPX change? (Part C)
3. What dynamic did the volatility index follow? (Parts B, D)
4. When did the market rebound, and how did that show in option prices? (Parts A, E)
5. Our extension: the fear premium (risk-neutral Q minus real-world P), split into a
   volatility part and a crash part, and the fake-vs-real pause comparison. (Part E)

## Repository layout

| Folder | What it does | Tool |
|---|---|---|
| `Part_A_events/` | Verifies when each of the 24 headlines actually moved ES futures | Python notebook |
| `Part_B_implied_vol/` | Implied vol at five moments, the smile, and our own volatility index against VIX | Python notebook |
| `Part_C_distribution/` | Risk-neutral distribution and crash probabilities (Breeden-Litzenberger) | Python notebook |
| `Part_D_realized_vol/` | Realized volatility, jump share and overnight gaps from 5-minute futures returns | Excel |
| `Part_E_models/` | Model ladder (Black-Scholes, Merton, Heston, SABR, Bates), Girsanov test, fear premium, fake vs real pause, leak test | Python package, see its own README |
| `report/` | The final report (PDF) | |

Part E prices options with [quantlab](https://github.com/solven139/quantlab), a C++/Python
pricing library (COS method, Heston and Bates characteristic functions, pooled calibration).

## Data

The data was provided by the course and is not in this repository:

- `RTH.zip`, `ETH.zip`: 3-second quotes for SPX options (strikes 4600-6600, one expiry per
  day), ES futures, SPX and VIX, in regular and extended hours.
- `2025_Liberation_Day_Tariff_Main_Events.csv`: 24 headlines with listed times.

Known limits: the lowest strike is 4600, so the left tail is cut off on 4 and 8 April; the
ETH file for the night of 9 April is empty; expiry switches from 16 April to 15 May on 7 April.

## Conventions shared by all parts

- Times are New York time.
- Futures and option prices are mids, (bid + ask) / 2. A quote of -1 means no quote.
- Rate 4.3%; discount factor D = exp(-0.043 T); T in years to 16:00 on expiry day.
- Forward from put-call parity at the strike where call and put are closest: F = K + (C - P) / D.
- Five snapshot moments: 1 Apr 15:55, 3 Apr 10:00, 4 Apr 15:55, 8 Apr 15:55, 9 Apr 15:55.
- Pause headlines (verified in Part A): fake 7 Apr 10:10, real 9 Apr 13:18.

## Team

| Part | Owner |
|---|---|
| A: Events and timing | Ramsai Talluri |
| B: Implied volatility and volatility index | Nguyen Minh Ha |
| C: Risk-neutral distribution | Toh Han Wei |
| D: Realized volatility | Tay Shi Hui |
| E: Models, fear premium, report  | Chen Pei Hsin Scott |
