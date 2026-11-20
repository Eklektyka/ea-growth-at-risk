"""
Stage 1 (continued): Clean and merge CISS and GDP data into a quarterly panel.
"""

import os
import csv
import math
from collections import defaultdict

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
CLEAN_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def parse_quarter(date_str):
    """Convert 'YYYY-QN' to (year, quarter) tuple."""
    parts = date_str.split('-Q')
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    return None


def date_to_quarter(date_str):
    """Convert 'YYYY-MM-DD' to (year, quarter) tuple."""
    parts = date_str.split('-')
    if len(parts) >= 2:
        y, m = int(parts[0]), int(parts[1])
        q = (m - 1) // 3 + 1
        return y, q
    return None


def load_ciss():
    """Load CISS daily data and aggregate to quarterly averages."""
    filepath = os.path.join(RAW_DIR, 'ciss_daily.csv')
    quarterly = defaultdict(list)

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get('OBS_VALUE', '').strip()
            date = row.get('TIME_PERIOD', '').strip()
            if not val or not date:
                continue
            try:
                v = float(val)
            except ValueError:
                continue
            yq = date_to_quarter(date)
            if yq:
                quarterly[yq].append(v)

    # Compute quarterly averages
    result = {}
    for yq, vals in sorted(quarterly.items()):
        result[yq] = sum(vals) / len(vals)
    return result


def load_gdp():
    """Load quarterly GDP levels and compute annualised q-o-q log growth."""
    filepath = os.path.join(RAW_DIR, 'gdp_quarterly.csv')
    levels = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = row.get('OBS_VALUE', '').strip()
            date = row.get('TIME_PERIOD', '').strip()
            if not val or not date:
                continue
            try:
                v = float(val)
            except ValueError:
                continue
            yq = parse_quarter(date)
            if yq:
                levels[yq] = v

    # Compute annualised q-o-q log growth: 4 * ln(GDP_t / GDP_{t-1})
    sorted_quarters = sorted(levels.keys())
    growth = {}
    for i in range(1, len(sorted_quarters)):
        curr = sorted_quarters[i]
        prev = sorted_quarters[i - 1]
        if levels[prev] > 0 and levels[curr] > 0:
            growth[curr] = 4.0 * math.log(levels[curr] / levels[prev]) * 100  # in percent
    return growth


def next_quarter(yq):
    y, q = yq
    if q == 4:
        return (y + 1, 1)
    return (y, q + 1)


def build_forward_growth(growth, h):
    """Compute average annualised growth over the next h quarters."""
    sorted_q = sorted(growth.keys())
    qset = set(sorted_q)
    result = {}
    for q in sorted_q:
        vals = []
        fq = next_quarter(q)
        for _ in range(h):
            if fq in growth:
                vals.append(growth[fq])
            else:
                break
            fq = next_quarter(fq)
        if len(vals) == h:
            result[q] = sum(vals) / len(vals)
    return result


def main():
    print("Loading CISS...")
    ciss = load_ciss()
    print(f"  {len(ciss)} quarterly observations, {min(ciss.keys())} to {max(ciss.keys())}")

    print("Loading GDP...")
    growth = load_gdp()
    print(f"  {len(growth)} quarterly growth observations, {min(growth.keys())} to {max(growth.keys())}")

    # Merge
    common_quarters = sorted(set(ciss.keys()) & set(growth.keys()))
    print(f"  {len(common_quarters)} common quarters: {common_quarters[0]} to {common_quarters[-1]}")

    # Build forward growth for h=1 and h=4
    fwd1 = build_forward_growth(growth, 1)
    fwd4 = build_forward_growth(growth, 4)

    # Save merged dataset
    outpath = os.path.join(CLEAN_DIR, 'panel.csv')
    with open(outpath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['year', 'quarter', 'yq', 'ciss', 'gdp_growth', 'fwd_growth_h1', 'fwd_growth_h4'])
        for yq in common_quarters:
            y, q = yq
            yq_str = f"{y}Q{q}"
            writer.writerow([
                y, q, yq_str,
                f"{ciss[yq]:.6f}",
                f"{growth[yq]:.4f}",
                f"{fwd1[yq]:.4f}" if yq in fwd1 else '',
                f"{fwd4[yq]:.4f}" if yq in fwd4 else '',
            ])

    print(f"Panel saved to {outpath}")
    # Print sample stats
    ciss_vals = [ciss[q] for q in common_quarters]
    growth_vals = [growth[q] for q in common_quarters]
    print(f"  CISS: mean={sum(ciss_vals)/len(ciss_vals):.4f}, min={min(ciss_vals):.4f}, max={max(ciss_vals):.4f}")
    print(f"  Growth: mean={sum(growth_vals)/len(growth_vals):.4f}, min={min(growth_vals):.4f}, max={max(growth_vals):.4f}")
    return True


if __name__ == '__main__':
    main()
