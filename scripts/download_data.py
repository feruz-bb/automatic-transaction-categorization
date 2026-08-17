"""Fetch the FIN-001 raw dataset from Hugging Face into data/raw/.

The raw CSV is NOT committed to Git (see .gitignore); this script is how anyone —
including a grader reproducing the project — obtains it. The dataset is openly
downloadable (MIT license, no authentication), which is the whole reason it was chosen
over gated alternatives.

    python scripts/download_data.py

Verifies the row count after download so a truncated file fails loudly instead of
silently corrupting every downstream step.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

URL = (
    "https://huggingface.co/datasets/DoDataThings/"
    "us-bank-transaction-categories-v2/resolve/main/transactions-synthetic.csv"
)
DEST = Path(__file__).resolve().parents[1] / "data" / "raw" / "transactions-synthetic.csv"
EXPECTED_ROWS = 68000  # 68,001 lines including the header


def main() -> int:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading:\n  {URL}\n-> {DEST}")
    urllib.request.urlretrieve(URL, DEST)

    with DEST.open("r", encoding="utf-8") as fh:
        lines = sum(1 for _ in fh)
    rows = lines - 1  # header
    print(f"Downloaded {rows:,} data rows ({DEST.stat().st_size/1e6:.1f} MB).")

    if rows != EXPECTED_ROWS:
        print(
            f"ERROR: expected {EXPECTED_ROWS:,} rows, got {rows:,}. "
            "The file may be truncated or the source changed — do not proceed.",
            file=sys.stderr,
        )
        return 1
    print("Row count verified. Data ready at data/raw/transactions-synthetic.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
