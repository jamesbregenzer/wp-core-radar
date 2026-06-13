from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
RAW_MANUAL = ROOT / "data" / "raw" / "manual"

QUERY_NAME = sys.argv[1] if len(sys.argv) > 1 else "manual_query"

source = DOWNLOADS / "query.csv"

if not source.exists():
    raise SystemExit(f"Could not find {source}")

today = datetime.now().strftime("%Y-%m-%d")
target_dir = RAW_MANUAL / today
target_dir.mkdir(parents=True, exist_ok=True)

target = target_dir / f"{QUERY_NAME}.csv"
shutil.copy2(source, target)

print(f"Imported {source}")
print(f"Saved to {target.relative_to(ROOT)}")
