from pathlib import Path
import subprocess
import time
import sys

DOWNLOADS = Path.home() / "Downloads"
ROOT = Path(__file__).resolve().parents[1]

QUERIES = {
    "media_has_patch": "https://core.trac.wordpress.org/query?status=!closed&component=Media&keywords=~has-patch&format=csv",
}

def wait_for_download(timeout=60):
    target = DOWNLOADS / "query.csv"
    partial = DOWNLOADS / "query.csv.part"

    start = time.time()
    while time.time() - start < timeout:
        if target.exists() and not partial.exists():
            return target
        time.sleep(1)

    raise TimeoutError("Timed out waiting for query.csv download")

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "media_has_patch"

    if name not in QUERIES:
        raise SystemExit(f"Unknown query: {name}")

    for file in DOWNLOADS.glob("query*.csv"):
        file.unlink()

    url = QUERIES[name]
    print(f"Opening Firefox for {name}...")
    subprocess.run(["open", "-a", "Firefox", url], check=True)

    downloaded = wait_for_download()
    print(f"Downloaded {downloaded}")

    subprocess.run(
        ["python3", str(ROOT / "scripts" / "import-download.py"), name],
        check=True
    )

    downloaded.unlink()
    print("Removed downloaded query.csv")

    subprocess.run(["osascript", "-e", 'tell application "Firefox" to quit'], check=False)
    print("Closed Firefox")

if __name__ == "__main__":
    main()
