# Decisions

## 1. Paper specification

I accessed the full text of the ECB Working Paper (No. 2458) and
confirmed the specification:

- **Dependent variable**: 100 × (y_{t+4} − y_t) where y_t = ln(real GDP),
  i.e. year-on-year log GDP growth in percentage points.
- **Regressors (univariate, Table 2)**: constant + financial indicator
  (one at a time).
- **Regressors (bivariate, Table A2)**: constant + current-quarter log
  GDP growth + financial indicator.
- **Quantiles**: 10th, 50th, 90th (not 5th/95th — small sample, footnote 2).
- **Sample**: 1999Q1 to 2018Q2.

I replicate both the univariate and bivariate CISS specifications with
these exact choices. Results are in `results/paper_spec.csv`.

I also run an extended quantile grid (5th through 95th percentile, h=1
and h=4) in `results/coefficients.csv`. This uses annualised q-o-q
growth as the dependent variable and a sample ending at 2018Q4. At h=4,
the annualised q-o-q dependent variable is algebraically identical to
the paper's year-on-year growth (the average of four annualised q-o-q
log growth rates telescopes to the cumulative log growth). The GDP
growth regressor in the extended grid is in annualised units (4× the
paper's), which rescales that coefficient by 1/4 but does not affect the
CISS coefficient.

## 2. GDP data source

Eurostat API returned 400 errors for all attempted URL patterns. Used
ECB MNA dataset instead (EA19, chain-linked volumes, calendar and
seasonally adjusted). This is the same underlying data but may differ at
the margin due to rounding or revision timing.

## 3. Euro area composition

The ECB GDP series uses I8 = Euro area 19 (fixed composition). The CISS
uses U2 = Euro area (changing composition). This is a minor inconsistency,
noted but not resolved.

## 4. CISS series version

This replication uses the "new CISS" (series key SS_CIN) as currently
served by the ECB Data Portal. The paper cites the original CISS of
Holló et al. (2012). The ECB has since revised the CISS methodology and
back-filled historical values. This is a plausible candidate for the
remaining coefficient gaps (especially at the OLS and median, which are
more sensitive to moderate changes in the regressor), but I have not
tested this directly.

## 5. Confidence intervals

Using statsmodels QuantReg with kernel (Powell) sandwich standard errors,
reporting 90% confidence intervals. The paper uses bootstrap with 1000
replications (Stata `sqreg`).

## 6. Candidate reasons for remaining gaps

The bivariate Q10 coefficient is close to the paper's (−16.91 vs −16.51).
The OLS and median are smaller in absolute value (OLS: −3.48 vs −5.93;
Q50: −1.50 vs −3.04). Plausible candidates:

1. CISS series version (new vs original)
2. GDP data revisions since 2020
3. Quarterly averaging method (I average all daily CISS values; the
   paper may use a different aggregation)
4. Sample end (for the extended grid only: 2018Q4 vs 2018Q2)

I do not claim to know which factor is responsible.
