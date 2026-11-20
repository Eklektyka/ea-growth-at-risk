# Growth-at-Risk in the Euro Area: A Replication Exercise

A small replication of the main result from Figueres & Jarociński (2020),
"Vulnerable growth in the Euro Area: Measuring the financial conditions,"
*Economics Letters* 191 (also ECB Working Paper No. 2458).

## What the paper shows

The paper finds that financial stress — measured by the ECB's Composite
Indicator of Systemic Stress (CISS) — affects the lower tail of the
future GDP growth distribution much more than the median or upper tail.
When financial stress rises, downside risks to growth increase sharply,
but the most likely growth outcome barely changes. Among ten euro area
financial indicators tested, the CISS is the most informative about tail
risks to growth.

## What this replication does

I estimate quantile regressions of one-year-ahead real GDP growth on
the CISS, following the paper's equation (1):

> y_{t+4} − y_t = α + β · x_t + u_t

where y_t is 100 × log(real GDP). I run two specifications:

1. **Univariate** (paper Table 2): regress year-ahead growth on a
   constant and the CISS only.
2. **Bivariate** (paper Table A2): add current-quarter log GDP growth
   (y_t − y_{t-1}) as a control.

Quantiles: τ = 0.10, 0.50, 0.90, plus OLS — matching the paper, which
uses these three quantiles rather than the 5th/95th because of the small
sample (footnote 2, p. 9).

I also estimate an extended quantile grid (τ = 0.05, 0.10, 0.25, 0.50,
0.75, 0.90, 0.95) with horizons h = 1 and h = 4, using annualised
quarter-on-quarter growth as the dependent variable. These additional
results are in `results/coefficients.csv`; see the
[Appendix](#appendix-extended-quantile-grid) below.

## Data

| Series | Source | Frequency | Sample |
|--------|--------|-----------|--------|
| CISS (Composite Indicator of Systemic Stress) | ECB Data Portal, series CISS.D.U2.Z0Z.4F.EC.SS_CIN.IDX | Daily, averaged to quarterly | 1980 Q1 – 2026 Q4 |
| Real GDP (chain-linked volumes, SA+CA) | ECB MNA dataset, EA19 fixed composition | Quarterly | 1995 Q1 – 2024 Q1 |

The paper's estimation sample runs from 1999 Q1 to 2018 Q2 (78
quarterly observations). I match this exactly for the paper-specification
regressions in `results/paper_spec.csv`.

## Key results: comparison with the paper

All numbers in the "Replication" rows come from `results/paper_spec.csv`.

### Table 2 (univariate): CISS coefficient on year-ahead GDP growth

|  | OLS | Q10 | Q50 | Q90 |
|--|-----|-----|-----|-----|
| **Paper** | −6.61 | −16.26 | −6.62 | −2.41 |
| **Replication** | −4.69 | −14.98 | −4.76 | −2.22 |

### Table A2 (bivariate, controlling for current GDP growth): CISS coefficient

|  | OLS | Q10 | Q50 | Q90 |
|--|-----|-----|-----|-----|
| **Paper** | −5.93 | −16.51 | −3.04 | −1.17 |
| **Replication** | −3.48 | −16.91 | −1.50 | −0.27 |

### Interpretation

The main qualitative result reproduces: the 10th percentile CISS
coefficient is far more negative than the median or 90th percentile
coefficient, in both specifications.

In the bivariate specification, the Q10 estimate (−16.91) is close to
the paper's (−16.51). The OLS and median estimates are smaller in
absolute value than the paper's (OLS: −3.48 vs −5.93; Q50: −1.50 vs
−3.04). In the univariate specification the gap is narrower but the same
pattern holds (Q10: −14.98 vs −16.26).

## Candidate reasons for remaining gaps

I do not claim to know which factor is responsible for the differences
between my estimates and the paper's, but the following are plausible
candidates:

1. **CISS series version.** This replication uses the "new CISS" (series
   SS_CIN, as currently served by the ECB Data Portal). The paper cites
   the original CISS of Holló et al. (2012). The ECB has revised the
   CISS methodology and back-filled historical values; daily values and
   therefore quarterly averages may differ.
2. **GDP data revisions.** National accounts have been revised multiple
   times since 2020 (benchmark revisions, ESA methodology updates). The
   paper used the vintage available circa 2019–2020.
3. **Quarterly averaging of a daily series.** I average all available
   daily CISS observations within each quarter. The paper may have used
   end-of-quarter values or a different aggregation rule (not stated
   explicitly).
4. **Sample end.** The paper's sample ends at 2018 Q2. I match this for
   the paper-specification run. The extended results in
   `results/coefficients.csv` use 1999 Q1 – 2018 Q4.

## Out-of-sample extension (2019 Q1 – 2023 Q1)

Coefficients estimated to 2018 Q4 are frozen and used to produce
quantile forecasts for subsequent quarters. I evaluate the quantile
(tick) loss at τ = 0.05 and τ = 0.50 against a benchmark that omits
CISS (numbers from `results/out_of_sample.csv`).

| Quantile | Sample | Tick loss (with CISS) | Tick loss (no CISS) | Ratio |
|----------|--------|----------------------|---------------------|-------|
| τ = 0.05 | All 17 quarters | 1.72 | 2.47 | 0.70 |
| τ = 0.05 | Excl. pandemic (13 quarters) | 1.98 | 1.32 | 1.50 |
| τ = 0.50 | All 17 quarters | 2.55 | 2.97 | 0.86 |
| τ = 0.50 | Excl. pandemic (13 quarters) | 1.60 | 1.67 | 0.96 |

Including the pandemic quarters (2020 Q1 – Q4), the CISS model reduces
the 5th-percentile tick loss by about 30% relative to the benchmark.
Once the pandemic is excluded, the CISS model is worse than the
benchmark at the 5th percentile (ratio 1.50). The pandemic quarters —
when CISS spiked and growth collapsed — are the main driver of the
out-of-sample gain. At the median, CISS adds modest value in both
subsamples.

The out-of-sample period ends at 2023 Q1 because the dependent variable
is average growth over the next four quarters and the GDP data extends
to 2024 Q1 (the latest available from the ECB MNA dataset at the time
of download).

## Differences from the paper

1. **CISS series version**: see above.
2. **GDP data source**: GDP comes from the ECB (MNA dataset, EA19 fixed
   composition) rather than Eurostat, because the Eurostat API returned
   errors during download. This is the same underlying data but may
   differ at the margin due to rounding or revision timing.
3. **Confidence intervals**: I use kernel (Powell) sandwich standard
   errors from statsmodels. The paper uses bootstrap with 1000
   replications (Stata `sqreg`).
4. **Euro area composition**: The CISS uses U2 (changing composition);
   the GDP uses I8 (EA19 fixed composition). This is a minor
   inconsistency.

## Limitations

- This is a teaching exercise, not a full replication. I estimate
  only the CISS specification, not the nine other financial indicators
  the paper compares.
- The out-of-sample evaluation covers only 17 quarters (13 excluding
  the pandemic), too few for strong statistical conclusions.
- Standard errors are not corrected for the overlap in the h = 4
  dependent variable (Newey-West or similar corrections would be
  appropriate in a fuller analysis).
- The nonlinearity test of Adrian et al. (2019) that the paper uses to
  show the Q10 coefficient is significantly different from the OLS
  coefficient is not performed here.

## Reproducing

```bash
pip install -r requirements.txt
python run_all.py
```

All random seeds are fixed. Output goes to `results/` and `figures/`.

---

## Appendix: extended quantile grid

The file `results/coefficients.csv` contains estimates for quantiles
τ = 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95 at horizons h = 1 and
h = 4, using the bivariate specification (constant + annualised q-o-q
GDP growth + CISS), sample 1999 Q1 – 2018 Q4 (80 observations).

The paper avoids the 5th and 95th percentiles because the sample is
small (footnote 2, p. 9: "We consider the 10th and 90th quantile, not
5th and 95th as in Adrian et al. (2019), as our sample is smaller").
The extended estimates at these extreme quantiles should be interpreted
with that caveat in mind.

Note that the annualised q-o-q dependent variable used in
`coefficients.csv` is algebraically equivalent to the year-on-year log
growth used in `paper_spec.csv` when h = 4 (the average of four
annualised q-o-q log growth rates telescopes to 100 × ln(GDP_{t+4} /
GDP_t)). The coefficients differ because the extended grid uses a later
sample end (2018 Q4 vs 2018 Q2) and because the GDP growth regressor is
in annualised units (4× the paper's current-quarter growth), which
rescales the coefficient on that variable by a factor of 1/4 but does
not affect the CISS coefficient.
