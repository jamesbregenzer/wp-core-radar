from pathlib import Path
import json
import subprocess
import time
import sys

DOWNLOADS = Path.home() / "Downloads"
ROOT = Path(__file__).resolve().parents[1]

def load_queries():
    config_path = ROOT / "config" / "queries.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Missing query config: {config_path}")

    with config_path.open() as file:
        config = json.load(file)

    queries = {}

    for query in config.get("queries", []):
        slug = query.get("slug")
        track = query.get("track")

        if not slug or not track:
            continue

        url = f"https://core.trac.wordpress.org/query?status=!closed&keywords=~{track}&format=csv"
        queries[slug] = url

    return queries

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

    queries = load_queries()

    if name not in queries:
        raise SystemExit(f"Unknown query: {name}")

    for file in DOWNLOADS.glob("query*.csv"):
        file.unlink()

    url = queries[name]
    print(f"Opening Firefox for {name}...")
    subprocess.run(["open", "-n", "-a", "Firefox", "--args", url], check=True)

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
