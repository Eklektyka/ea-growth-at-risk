"""
Stage 1: Download CISS and GDP data from official sources.
"""

import os
import datetime
import urllib.request
import ssl

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
SOURCES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'SOURCES.md')

os.makedirs(RAW_DIR, exist_ok=True)


def download(url, filename, description):
    """Download a URL and save to data/raw/. Returns (success, filepath, timestamp, url)."""
    filepath = os.path.join(RAW_DIR, filename)
    ts = datetime.datetime.now().isoformat()
    print(f"Downloading {description} from {url} ...")
    try:
        req = urllib.request.Request(url, headers={'Accept': 'text/csv, application/csv, */*'})
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=90) as resp:
            data = resp.read()
        with open(filepath, 'wb') as f:
            f.write(data)
        size = len(data)
        print(f"  OK: {size} bytes saved to {filepath}")
        return True, filepath, ts, url
    except Exception as e:
        print(f"  FAILED: {e}")
        return False, filepath, ts, url


def download_ciss():
    """Download ECB CISS daily data."""
    url1 = "https://data-api.ecb.europa.eu/service/data/CISS/D.U2.Z0Z.4F.EC.SS_CIN.IDX?format=csvdata"
    ok, fp, ts, url = download(url1, "ciss_daily.csv", "ECB CISS")
    return ok, fp, ts, url


def download_gdp():
    """Download euro area real GDP from Eurostat."""
    # Eurostat bulk download API
    url1 = ("https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
            "namq_10_gdp/Q.CLV2015.SCA.B1GQ.EA20"
            "?format=SDMX-CSV&compressed=false")
    ok, fp, ts, url = download(url1, "gdp_quarterly.csv", "Eurostat GDP (EA20)")
    if ok:
        return ok, fp, ts, url

    # Try EA19
    url2 = ("https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
            "namq_10_gdp/Q.CLV2015.SCA.B1GQ.EA19"
            "?format=SDMX-CSV&compressed=false")
    ok, fp, ts, url = download(url2, "gdp_quarterly.csv", "Eurostat GDP (EA19)")
    if ok:
        return ok, fp, ts, url

    # Fallback: Try different Eurostat format with dots
    url3 = ("https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
            "namq_10_gdp/Q.CLV2015.SCA.B1GQ.EA"
            "?format=SDMX-CSV&compressed=false")
    ok, fp, ts, url = download(url3, "gdp_quarterly.csv", "Eurostat GDP (EA)")
    if ok:
        return ok, fp, ts, url

    # ECB fallback: real GDP level
    url4 = ("https://data-api.ecb.europa.eu/service/data/MNA/"
            "Q.Y.I8.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.N"
            "?format=csvdata")
    ok, fp, ts, url = download(url4, "gdp_quarterly.csv", "ECB GDP level (fallback)")
    return ok, fp, ts, url


def main():
    sources = []

    ciss_ok, ciss_fp, ciss_ts, ciss_url = download_ciss()
    sources.append(("CISS", ciss_url, ciss_ts, "OK" if ciss_ok else "FAILED"))

    gdp_ok, gdp_fp, gdp_ts, gdp_url = download_gdp()
    sources.append(("GDP", gdp_url, gdp_ts, "OK" if gdp_ok else "FAILED"))

    # Write SOURCES.md
    with open(SOURCES_PATH, 'w') as f:
        f.write("# Data Sources\n\n")
        for name, url, ts, status in sources:
            f.write(f"## {name}\n- URL: {url}\n- Downloaded: {ts}\n- Status: {status}\n\n")

    if not ciss_ok or not gdp_ok:
        blocked = os.path.join(os.path.dirname(__file__), '..', 'BLOCKED.md')
        with open(blocked, 'w') as f:
            f.write("# BLOCKED\n\n")
            if not ciss_ok:
                f.write("CISS download failed from all attempted URLs.\n")
            if not gdp_ok:
                f.write("GDP download failed from all attempted URLs.\n")
        print("BLOCKED: not all data downloaded successfully.")
        return False

    print("All data downloaded successfully.")
    return True


if __name__ == '__main__':
    main()
