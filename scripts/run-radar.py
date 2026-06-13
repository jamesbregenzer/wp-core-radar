from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def run(command):
    print(f"\n→ {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)

def main():
    print("WP Core Radar")
    print("Running browser-assisted collection and report generation.")

    run(["python3", "scripts/browser-fetch.py", "media_has_patch"])
    run(["python3", "scripts/generate-report.py"])

    print("\nLatest report:")
    print((ROOT / "reports" / "latest.md").read_text().split("## Top Opportunities")[0])

    run(["git", "status", "--short"])

    print("\nDone.")

if __name__ == "__main__":
    main()
