"""
Stage 3: Out-of-sample evaluation.

Freeze coefficients estimated to 2018Q4 and produce quantile forecasts
for 2019Q1 to latest available quarter. Evaluate tick loss.
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

TAUS_EVAL = [0.05, 0.50]
H = 4  # focus on h=4 as in the paper
SAMPLE_START = (1999, 1)
SAMPLE_END = (2018, 4)
OOS_START = (2019, 1)
PANDEMIC_START = (2020, 1)
PANDEMIC_END = (2020, 4)


def load_panel():
    rows = []
    with open(DATA_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def yq_tuple(row):
    return (int(row['year']), int(row['quarter']))


def tick_loss(y, q_hat, tau):
    """Quantile (tick/check) loss function."""
    e = y - q_hat
    return np.where(e >= 0, tau * e, (tau - 1) * e)


def main():
    rows = load_panel()
    horizon_key = f'fwd_growth_h{H}'

    # Split into in-sample and out-of-sample
    in_sample = [r for r in rows if SAMPLE_START <= yq_tuple(r) <= SAMPLE_END and r[horizon_key]]
    oos = [r for r in rows if yq_tuple(r) >= OOS_START and r[horizon_key]]

    print(f"In-sample: {len(in_sample)} obs ({in_sample[0]['yq']} to {in_sample[-1]['yq']})")
    print(f"Out-of-sample: {len(oos)} obs ({oos[0]['yq']} to {oos[-1]['yq']})")

    # Prepare in-sample data
    y_in = np.array([float(r[horizon_key]) for r in in_sample])
    gdp_in = np.array([float(r['gdp_growth']) for r in in_sample])
    ciss_in = np.array([float(r['ciss']) for r in in_sample])
    X_in = sm.add_constant(np.column_stack([gdp_in, ciss_in]))
    X_in_nociss = sm.add_constant(gdp_in)

    # Prepare OOS data
    y_oos = np.array([float(r[horizon_key]) for r in oos])
    gdp_oos = np.array([float(r['gdp_growth']) for r in oos])
    ciss_oos = np.array([float(r['ciss']) for r in oos])
    X_oos = sm.add_constant(np.column_stack([gdp_oos, ciss_oos]))
    X_oos_nociss = sm.add_constant(gdp_oos)
    quarters_oos = [r['yq'] for r in oos]
    yq_tuples_oos = [yq_tuple(r) for r in oos]

    # Pandemic mask
    pandemic_mask = np.array([PANDEMIC_START <= yq <= PANDEMIC_END for yq in yq_tuples_oos])
    no_pandemic_mask = ~pandemic_mask

    results = []

    for tau in TAUS_EVAL:
        # Full model (with CISS)
        mod_full = sm.QuantReg(y_in, X_in).fit(q=tau, max_iter=5000)
        q_hat_full = mod_full.predict(X_oos)

        # Benchmark (no CISS)
        mod_bench = sm.QuantReg(y_in, X_in_nociss).fit(q=tau, max_iter=5000)
        q_hat_bench = mod_bench.predict(X_oos_nociss)

        # Tick losses
        loss_full_all = tick_loss(y_oos, q_hat_full, tau)
        loss_bench_all = tick_loss(y_oos, q_hat_bench, tau)
        loss_full_nopand = tick_loss(y_oos[no_pandemic_mask], q_hat_full[no_pandemic_mask], tau)
        loss_bench_nopand = tick_loss(y_oos[no_pandemic_mask], q_hat_bench[no_pandemic_mask], tau)

        avg_full_all = np.mean(loss_full_all)
        avg_bench_all = np.mean(loss_bench_all)
        avg_full_nopand = np.mean(loss_full_nopand)
        avg_bench_nopand = np.mean(loss_bench_nopand)

        print(f"\ntau={tau:.2f}:")
        print(f"  All periods:        Full={avg_full_all:.4f}, Benchmark={avg_bench_all:.4f}, "
              f"Ratio={avg_full_all/avg_bench_all:.4f}")
        print(f"  Excl. pandemic:     Full={avg_full_nopand:.4f}, Benchmark={avg_bench_nopand:.4f}, "
              f"Ratio={avg_full_nopand/avg_bench_nopand:.4f}")

        for label, full_loss, bench_loss in [
            ('all_periods', avg_full_all, avg_bench_all),
            ('excl_pandemic', avg_full_nopand, avg_bench_nopand),
        ]:
            results.append({
                'tau': tau,
                'h': H,
                'sample': label,
                'n': len(y_oos) if label == 'all_periods' else int(no_pandemic_mask.sum()),
                'tick_loss_full': avg_full_all if label == 'all_periods' else avg_full_nopand,
                'tick_loss_benchmark': avg_bench_all if label == 'all_periods' else avg_bench_nopand,
                'loss_ratio': (avg_full_all / avg_bench_all) if label == 'all_periods' else (avg_full_nopand / avg_bench_nopand),
            })

    # Save results
    outpath = os.path.join(RESULTS_DIR, 'out_of_sample.csv')
    with open(outpath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['tau', 'h', 'sample', 'n',
                                                'tick_loss_full', 'tick_loss_benchmark', 'loss_ratio'])
        writer.writeheader()
        for r in results:
            writer.writerow({
                'tau': r['tau'],
                'h': r['h'],
                'sample': r['sample'],
                'n': r['n'],
                'tick_loss_full': f"{r['tick_loss_full']:.6f}",
                'tick_loss_benchmark': f"{r['tick_loss_benchmark']:.6f}",
                'loss_ratio': f"{r['loss_ratio']:.6f}",
            })
    print(f"\nResults saved to {outpath}")

    # Plot OOS 5th percentile forecast
    # Re-estimate tau=0.05 for the plot
    mod_05 = sm.QuantReg(y_in, X_in).fit(q=0.05, max_iter=5000)
    mod_50 = sm.QuantReg(y_in, X_in).fit(q=0.50, max_iter=5000)
    q05_oos = mod_05.predict(X_oos)
    q50_oos = mod_50.predict(X_oos)

    # Benchmark
    mod_05_b = sm.QuantReg(y_in, X_in_nociss).fit(q=0.05, max_iter=5000)
    q05_bench = mod_05_b.predict(X_oos_nociss)

    fig, ax = plt.subplots(figsize=(12, 5))
    x = range(len(quarters_oos))

    ax.plot(x, y_oos, 'ko', markersize=4, label='Realised growth', zorder=5)
    ax.plot(x, q05_oos, 'r-', linewidth=2, label='5th pctile (with CISS)')
    ax.plot(x, q05_bench, 'r--', linewidth=1.5, alpha=0.6, label='5th pctile (no CISS)')
    ax.plot(x, q50_oos, 'b-', linewidth=1.5, label='Median (with CISS)')

    ax.fill_between(x, q05_oos, q50_oos, alpha=0.1, color='red')

    # Mark pandemic
    pandemic_idx = [i for i, yq in enumerate(yq_tuples_oos)
                    if PANDEMIC_START <= yq <= PANDEMIC_END]
    if pandemic_idx:
        ax.axvspan(pandemic_idx[0] - 0.5, pandemic_idx[-1] + 0.5,
                   alpha=0.15, color='gray', label='Pandemic quarters')

    ax.set_xticks(list(x))
    ax.set_xticklabels(quarters_oos, rotation=45, fontsize=8)
    ax.set_ylabel('Annualised GDP growth (%)')
    ax.set_title(f'Out-of-sample quantile forecasts (h={H}, coefficients frozen at 2018Q4)')
    ax.legend(fontsize=8)
    plt.tight_layout()

    outpath = os.path.join(FIGURES_DIR, 'out_of_sample_5pct.png')
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Figure saved to {outpath}")

    # Pandemic impact assessment
    print("\n" + "=" * 70)
    print("PANDEMIC IMPACT ASSESSMENT")
    print("=" * 70)
    if pandemic_mask.any():
        loss_pandemic_only = tick_loss(y_oos[pandemic_mask], q_hat_full[pandemic_mask], 0.05)
        loss_non_pandemic = tick_loss(y_oos[no_pandemic_mask], q_hat_full[no_pandemic_mask], 0.05)
        print(f"  tau=0.05 avg tick loss, pandemic quarters only: {np.mean(loss_pandemic_only):.4f}")
        print(f"  tau=0.05 avg tick loss, non-pandemic quarters:  {np.mean(loss_non_pandemic):.4f}")
        print(f"  Ratio pandemic/non-pandemic: {np.mean(loss_pandemic_only)/np.mean(loss_non_pandemic):.1f}x")
        print(f"  Pandemic quarters ({pandemic_mask.sum()} of {len(y_oos)}) "
              f"dominate the total loss if ratio >> 1.")


if __name__ == '__main__':
    main()
