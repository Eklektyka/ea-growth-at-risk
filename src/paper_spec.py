"""
Replicate the paper's exact specification:
  - LHS: 100 * (y_{t+4} - y_t), i.e. year-on-year log GDP growth
         (equals our fwd_growth_h4)
  - RHS univariate (Table 2):  constant + CISS
  - RHS bivariate (Table A2):  constant + current-quarter log growth + CISS
         (current-quarter growth = gdp_growth / 4 in our panel)
  - Sample: 1999Q1 to 2018Q2
  - Quantiles: 0.10, 0.50, 0.90 plus OLS
"""

import os
import csv
import numpy as np
import statsmodels.api as sm

np.random.seed(42)

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_PATH = os.path.join(BASE_DIR, 'data', 'panel.csv')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

TAUS = [0.10, 0.50, 0.90]
SAMPLE_START = (1999, 1)
SAMPLE_END = (2018, 2)


def load_panel():
    rows = []
    with open(DATA_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def yq(r):
    return (int(r['year']), int(r['quarter']))


def run_spec(label, y, X, var_names, taus):
    """Run OLS + quantile regressions, return list of result dicts."""
    results = []
    n = len(y)

    ols = sm.OLS(y, X).fit()
    for j, name in enumerate(var_names):
        ci = ols.conf_int(alpha=0.10)[j]
        results.append({
            'spec': label, 'tau': 'OLS', 'variable': name,
            'coefficient': ols.params[j], 'ci_lower': ci[0], 'ci_upper': ci[1], 'n': n,
        })
    coef_str = ', '.join(f'{name}={ols.params[j]:.3f}' for j, name in enumerate(var_names))
    print(f"  OLS: {coef_str}")

    for tau in taus:
        res = sm.QuantReg(y, X).fit(q=tau, max_iter=5000)
        for j, name in enumerate(var_names):
            ci = res.conf_int(alpha=0.10)[j]
            results.append({
                'spec': label, 'tau': tau, 'variable': name,
                'coefficient': res.params[j], 'ci_lower': ci[0], 'ci_upper': ci[1], 'n': n,
            })
        coef_str = ', '.join(f'{name}={res.params[j]:.3f}' for j, name in enumerate(var_names))
        print(f"  Q{int(tau*100):02d}: {coef_str}")

    return results


def main():
    rows = load_panel()

    # Filter to sample with fwd_growth_h4 available and within sample window
    sample = [r for r in rows
              if SAMPLE_START <= yq(r) <= SAMPLE_END and r['fwd_growth_h4']]

    n = len(sample)
    print(f"Sample: {n} obs ({sample[0]['yq']} to {sample[-1]['yq']})")

    # Variables in paper's units
    y = np.array([float(r['fwd_growth_h4']) for r in sample])  # = 100*(y_{t+4}-y_t)
    ciss = np.array([float(r['ciss']) for r in sample])
    current_growth = np.array([float(r['gdp_growth']) / 4.0 for r in sample])  # = 100*(y_t-y_{t-1})

    all_results = []

    # --- Univariate: Table 2 spec (CISS only, no GDP growth control) ---
    print("\n--- Univariate (Table 2 spec): LHS = y_{t+4}-y_t, RHS = const + CISS ---")
    X_uni = sm.add_constant(ciss)
    all_results.extend(run_spec('univariate', y, X_uni, ['const', 'ciss'], TAUS))

    # --- Bivariate: Table A2 spec (current growth + CISS) ---
    print("\n--- Bivariate (Table A2 spec): LHS = y_{t+4}-y_t, RHS = const + current_growth + CISS ---")
    X_biv = sm.add_constant(np.column_stack([current_growth, ciss]))
    all_results.extend(run_spec('bivariate', y, X_biv, ['const', 'current_growth', 'ciss'], TAUS))

    # Save
    outpath = os.path.join(RESULTS_DIR, 'paper_spec.csv')
    with open(outpath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['spec', 'tau', 'variable', 'coefficient',
                                                'ci_lower', 'ci_upper', 'n'])
        writer.writeheader()
        for r in all_results:
            writer.writerow({
                'spec': r['spec'],
                'tau': r['tau'],
                'variable': r['variable'],
                'coefficient': f"{r['coefficient']:.6f}",
                'ci_lower': f"{r['ci_lower']:.6f}",
                'ci_upper': f"{r['ci_upper']:.6f}",
                'n': r['n'],
            })
    print(f"\nSaved to {outpath}")

    # Print comparison table
    print("\n" + "=" * 70)
    print("COMPARISON WITH PAPER")
    print("=" * 70)

    print("\nTable 2 (univariate): CISS coefficient on year-ahead GDP growth")
    print(f"{'':>8}  {'OLS':>8}  {'Q10':>8}  {'Q50':>8}  {'Q90':>8}")
    paper_t2 = {'OLS': -6.61, 0.10: -16.26, 0.50: -6.62, 0.90: -2.41}
    ours_t2 = {}
    for r in all_results:
        if r['spec'] == 'univariate' and r['variable'] == 'ciss':
            ours_t2[r['tau']] = r['coefficient']
    print(f"{'Paper':>8}  {paper_t2['OLS']:>8.2f}  {paper_t2[0.10]:>8.2f}  {paper_t2[0.50]:>8.2f}  {paper_t2[0.90]:>8.2f}")
    print(f"{'Ours':>8}  {ours_t2['OLS']:>8.2f}  {ours_t2[0.10]:>8.2f}  {ours_t2[0.50]:>8.2f}  {ours_t2[0.90]:>8.2f}")

    print("\nTable A2 (bivariate, controlling for current growth): CISS coefficient")
    print(f"{'':>8}  {'OLS':>8}  {'Q10':>8}  {'Q50':>8}  {'Q90':>8}")
    paper_a2 = {'OLS': -5.93, 0.10: -16.51, 0.50: -3.04, 0.90: -1.17}
    ours_a2 = {}
    for r in all_results:
        if r['spec'] == 'bivariate' and r['variable'] == 'ciss':
            ours_a2[r['tau']] = r['coefficient']
    print(f"{'Paper':>8}  {paper_a2['OLS']:>8.2f}  {paper_a2[0.10]:>8.2f}  {paper_a2[0.50]:>8.2f}  {paper_a2[0.90]:>8.2f}")
    print(f"{'Ours':>8}  {ours_a2['OLS']:>8.2f}  {ours_a2[0.10]:>8.2f}  {ours_a2[0.50]:>8.2f}  {ours_a2[0.90]:>8.2f}")


if __name__ == '__main__':
    main()
