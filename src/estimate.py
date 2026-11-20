"""
Stage 2: Quantile regression estimation for Growth-at-Risk.

Dependent variable: average annualised GDP growth over the next h quarters.
Regressors: constant, current GDP growth, current CISS.
"""

import os
import csv
import numpy as np
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(42)

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DATA_PATH = os.path.join(BASE_DIR, 'data', 'panel.csv')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
FIGURES_DIR = os.path.join(BASE_DIR, 'figures')

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

TAUS = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
HORIZONS = [1, 4]
SAMPLE_START = (1999, 1)
SAMPLE_END = (2018, 4)


def load_panel():
    """Load panel data."""
    rows = []
    with open(DATA_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def filter_sample(rows, start, end, horizon_key):
    """Filter rows to sample period and require non-missing forward growth."""
    filtered = []
    for r in rows:
        y, q = int(r['year']), int(r['quarter'])
        yq = (y, q)
        if yq < start or yq > end:
            continue
        if not r[horizon_key]:
            continue
        filtered.append(r)
    return filtered


def run_quantile_regressions(rows, h, taus, sample_start, sample_end):
    """Run quantile regressions for a given horizon h."""
    horizon_key = f'fwd_growth_h{h}'
    sample = filter_sample(rows, sample_start, sample_end, horizon_key)

    n = len(sample)
    print(f"\nHorizon h={h}: {n} observations ({sample[0]['yq']} to {sample[-1]['yq']})")

    y = np.array([float(r[horizon_key]) for r in sample])
    gdp_growth = np.array([float(r['gdp_growth']) for r in sample])
    ciss = np.array([float(r['ciss']) for r in sample])
    X = sm.add_constant(np.column_stack([gdp_growth, ciss]))
    quarters = [r['yq'] for r in sample]

    results = []

    # OLS benchmark
    ols = sm.OLS(y, X).fit()
    for j, name in enumerate(['const', 'gdp_growth', 'ciss']):
        ci = ols.conf_int(alpha=0.10)[j]
        results.append({
            'tau': 'OLS',
            'h': h,
            'variable': name,
            'coefficient': ols.params[j],
            'ci_lower': ci[0],
            'ci_upper': ci[1],
            'n': n,
        })
    print(f"  OLS: const={ols.params[0]:.3f}, gdp={ols.params[1]:.3f}, ciss={ols.params[2]:.3f}")

    # Quantile regressions
    qr_models = {}
    for tau in taus:
        mod = sm.QuantReg(y, X)
        try:
            res = mod.fit(q=tau, max_iter=5000)
        except Exception as e:
            print(f"  tau={tau}: FAILED ({e})")
            continue

        qr_models[tau] = res

        for j, name in enumerate(['const', 'gdp_growth', 'ciss']):
            ci = res.conf_int(alpha=0.10)[j]
            results.append({
                'tau': tau,
                'h': h,
                'variable': name,
                'coefficient': res.params[j],
                'ci_lower': ci[0],
                'ci_upper': ci[1],
                'n': n,
            })
        print(f"  tau={tau:.2f}: const={res.params[0]:.3f}, gdp={res.params[1]:.3f}, ciss={res.params[2]:.3f}")

    return results, ols, qr_models, X, y, quarters


def save_coefficients(all_results):
    """Save coefficient table."""
    outpath = os.path.join(RESULTS_DIR, 'coefficients.csv')
    with open(outpath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['tau', 'h', 'variable', 'coefficient',
                                                'ci_lower', 'ci_upper', 'n'])
        writer.writeheader()
        for r in all_results:
            writer.writerow({
                'tau': r['tau'],
                'h': r['h'],
                'variable': r['variable'],
                'coefficient': f"{r['coefficient']:.6f}",
                'ci_lower': f"{r['ci_lower']:.6f}",
                'ci_upper': f"{r['ci_upper']:.6f}",
                'n': r['n'],
            })
    print(f"\nCoefficients saved to {outpath}")


def plot_ciss_coefficient_by_quantile(all_results):
    """Plot CISS coefficient across quantiles for h=1 and h=4."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for idx, h in enumerate(HORIZONS):
        ax = axes[idx]
        # Quantile regression coefficients
        qr_ciss = [(r['tau'], r['coefficient'], r['ci_lower'], r['ci_upper'])
                    for r in all_results
                    if r['h'] == h and r['variable'] == 'ciss' and r['tau'] != 'OLS']
        taus_plot = [x[0] for x in qr_ciss]
        coefs = [x[1] for x in qr_ciss]
        ci_lo = [x[2] for x in qr_ciss]
        ci_hi = [x[3] for x in qr_ciss]

        # OLS line
        ols_ciss = [r['coefficient'] for r in all_results
                    if r['h'] == h and r['variable'] == 'ciss' and r['tau'] == 'OLS']

        ax.fill_between(taus_plot, ci_lo, ci_hi, alpha=0.2, color='steelblue')
        ax.plot(taus_plot, coefs, 'o-', color='steelblue', label='Quantile regression')
        if ols_ciss:
            ax.axhline(ols_ciss[0], color='red', linestyle='--', label='OLS')
        ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlabel('Quantile (τ)')
        ax.set_ylabel('CISS coefficient')
        ax.set_title(f'CISS coefficient by quantile (h={h})')
        ax.legend()

    plt.tight_layout()
    outpath = os.path.join(FIGURES_DIR, 'ciss_coefficient_by_quantile.png')
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Figure saved to {outpath}")


def plot_fitted_quantiles(qr_models, ols, X, y, quarters, h):
    """Plot fitted 5%, 50%, 95% quantiles against realised growth."""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Convert quarter strings to indices for plotting
    x_ticks = list(range(len(quarters)))

    ax.plot(x_ticks, y, 'k.', markersize=3, label='Realised growth', alpha=0.7)

    colors = {0.05: 'red', 0.50: 'blue', 0.95: 'green'}
    for tau in [0.05, 0.50, 0.95]:
        if tau in qr_models:
            fitted = qr_models[tau].predict(X)
            ax.plot(x_ticks, fitted, color=colors[tau], linewidth=1.5,
                    label=f'τ = {tau:.2f}')

    # Shade between 5% and 95%
    if 0.05 in qr_models and 0.95 in qr_models:
        f05 = qr_models[0.05].predict(X)
        f95 = qr_models[0.95].predict(X)
        ax.fill_between(x_ticks, f05, f95, alpha=0.1, color='blue')

    # X-axis labels
    tick_step = max(1, len(quarters) // 15)
    ax.set_xticks(x_ticks[::tick_step])
    ax.set_xticklabels([quarters[i] for i in range(0, len(quarters), tick_step)], rotation=45)
    ax.set_ylabel('Annualised GDP growth (%)')
    ax.set_title(f'Fitted quantiles vs realised growth (h={h})')
    ax.legend()

    plt.tight_layout()
    outpath = os.path.join(FIGURES_DIR, f'fitted_quantiles_h{h}.png')
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Figure saved to {outpath}")


def assess_main_result(all_results):
    """Assess whether the paper's main qualitative result holds."""
    print("\n" + "=" * 70)
    print("ASSESSMENT: Does financial stress move lower quantiles more?")
    print("=" * 70)

    for h in HORIZONS:
        print(f"\n--- Horizon h={h} ---")
        ciss_coefs = {}
        for r in all_results:
            if r['h'] == h and r['variable'] == 'ciss' and r['tau'] != 'OLS':
                ciss_coefs[r['tau']] = r['coefficient']

        ols_ciss = [r['coefficient'] for r in all_results
                    if r['h'] == h and r['variable'] == 'ciss' and r['tau'] == 'OLS'][0]

        for tau in sorted(ciss_coefs.keys()):
            print(f"  tau={tau:.2f}: CISS coef = {ciss_coefs[tau]:.3f}")
        print(f"  OLS:      CISS coef = {ols_ciss:.3f}")

        # Check: are lower quantile coefficients more negative?
        low_coefs = [ciss_coefs[t] for t in [0.05, 0.10] if t in ciss_coefs]
        mid_coef = ciss_coefs.get(0.50, None)
        high_coefs = [ciss_coefs[t] for t in [0.90, 0.95] if t in ciss_coefs]

        if low_coefs and mid_coef is not None and high_coefs:
            avg_low = np.mean(low_coefs)
            avg_high = np.mean(high_coefs)
            result_holds = avg_low < mid_coef < avg_high or (abs(avg_low) > abs(mid_coef))
            print(f"\n  Average lower (5-10%) CISS coef: {avg_low:.3f}")
            print(f"  Median (50%) CISS coef: {mid_coef:.3f}")
            print(f"  Average upper (90-95%) CISS coef: {avg_high:.3f}")

            if avg_low < mid_coef:
                print("  => CISS has a MORE NEGATIVE effect on lower quantiles than the median.")
                print("     This is CONSISTENT with the paper's main result.")
            else:
                print("  => CISS does NOT have a more negative effect on lower quantiles.")
                print("     This DOES NOT support the paper's main result.")

    # Save assessment
    outpath = os.path.join(RESULTS_DIR, 'assessment.txt')
    with open(outpath, 'w') as f:
        for h in HORIZONS:
            f.write(f"Horizon h={h}:\n")
            ciss_coefs = {}
            for r in all_results:
                if r['h'] == h and r['variable'] == 'ciss' and r['tau'] != 'OLS':
                    ciss_coefs[r['tau']] = r['coefficient']
            for tau in sorted(ciss_coefs.keys()):
                f.write(f"  tau={tau:.2f}: CISS coef = {ciss_coefs[tau]:.3f}\n")

            low_coefs = [ciss_coefs[t] for t in [0.05, 0.10] if t in ciss_coefs]
            mid_coef = ciss_coefs.get(0.50, None)
            if low_coefs and mid_coef is not None:
                avg_low = np.mean(low_coefs)
                if avg_low < mid_coef:
                    f.write(f"  Result: CISS coefficient more negative at lower quantiles (avg 5-10%: {avg_low:.3f} vs median: {mid_coef:.3f}).\n")
                    f.write("  Consistent with the paper's main finding.\n")
                else:
                    f.write(f"  Result: CISS coefficient NOT more negative at lower quantiles.\n")
                    f.write("  Does not support the paper's main finding.\n")
            f.write("\n")
    print(f"\nAssessment saved to {outpath}")


def main():
    rows = load_panel()
    all_results = []

    for h in HORIZONS:
        results, ols, qr_models, X, y, quarters = run_quantile_regressions(
            rows, h, TAUS, SAMPLE_START, SAMPLE_END
        )
        all_results.extend(results)
        plot_fitted_quantiles(qr_models, ols, X, y, quarters, h)

    save_coefficients(all_results)
    plot_ciss_coefficient_by_quantile(all_results)
    assess_main_result(all_results)


if __name__ == '__main__':
    main()
