import json
from pathlib import Path
import matplotlib.pyplot as plt

RESULTS_DIR = Path("results")

def latest_result_file() -> Path:
    files = sorted(RESULTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No results JSON files found under results/")
    return files[0]

def main():
    path = latest_result_file()
    data = json.loads(path.read_text(encoding="utf-8"))

    measurements = data["data"]["measurements"]
    timestamps = data["data"]["timestamps_epoch"]

    # normalize time to start at 0 for plot readability
    t0 = timestamps[0]
    t = [x - t0 for x in timestamps]

    plt.figure()
    plt.plot(t, measurements)
    plt.title(f"Current over time ({data['ammeter_type']})")
    plt.xlabel("Time (s)")
    plt.ylabel("Current (A)")
    plt.tight_layout()

    out_png = RESULTS_DIR / f"{data['run_id']}.png"
    plt.savefig(out_png)
    print("Saved plot:", out_png)

if __name__ == "__main__":
    main()