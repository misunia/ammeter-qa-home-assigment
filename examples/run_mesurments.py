import threading
import time
import json
from pathlib import Path

import matplotlib.pyplot as plt

from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.client import request_current_from_ammeter

from src.testing.ammeter_framework import AmmeterTestFramework


# All results (json + plots) will be saved here
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


def start_emulators():
    # Start each ammeter emulator in a background thread.
    # Using daemon threads so they stop automatically when the script exits.
    threading.Thread(target=lambda: GreenleeAmmeter(5000).start_server(), daemon=True).start()
    threading.Thread(target=lambda: EntesAmmeter(5001).start_server(), daemon=True).start()
    threading.Thread(target=lambda: CircutorAmmeter(5002).start_server(), daemon=True).start()

    # Give the servers a moment to start listening on their ports
    time.sleep(2)


def load_result(path: Path) -> dict:
    # Helper to load a saved result json file
    return json.loads(path.read_text(encoding="utf-8"))


def plot_single(result: dict, out_path: Path):
    # Plot current values over time for a single ammeter run
    measurements = result["data"]["measurements"]
    timestamps = result["data"]["timestamps_epoch"]

    # Normalize time so the first sample starts at t=0
    t0 = timestamps[0]
    t = [x - t0 for x in timestamps]

    plt.figure()
    plt.plot(t, measurements)
    plt.title(f"Current over time ({result['ammeter_type']})")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Current (A)")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_comparison(results: dict[str, dict], out_path: Path):
    # Plot all ammeters on the same graph for comparison
    plt.figure()

    for ammeter_type, result in results.items():
        measurements = result["data"]["measurements"]
        timestamps = result["data"]["timestamps_epoch"]

        t0 = timestamps[0]
        t = [x - t0 for x in timestamps]

        plt.plot(t, measurements, label=ammeter_type)

    plt.title("Current over time – comparison")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Current (A)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def main():
    # Start all emulators before running any measurements
    start_emulators()

    # Create the test framework instance
    fw = AmmeterTestFramework("config/config.yaml", results_dir=str(RESULTS_DIR))

    ammeters = ["greenlee", "entes", "circutor"]
    collected_results: dict[str, dict] = {}

    print("Running duration-based sampling campaign...\n")

    for ammeter in ammeters:
        print(f"Sampling {ammeter}...")

        # Run a time-based sampling session
        result = fw.run_test(
            ammeter,
            request_current_from_ammeter,
            total_duration_seconds=3.0,
            sampling_frequency_hz=10.0,
            save=True,
        )

        collected_results[ammeter] = result

        # Save individual plot for this ammeter
        json_path = RESULTS_DIR / f"{result['run_id']}.json"
        png_path = RESULTS_DIR / f"{result['run_id']}.png"

        plot_single(result, png_path)

        print(f"  saved: {json_path.name}")
        print(f"  plot:  {png_path.name}\n")

    # Create a single comparison plot for all ammeters
    comparison_path = RESULTS_DIR / "comparison.png"
    plot_comparison(collected_results, comparison_path)

    print("Comparison plot saved:", comparison_path)
    print("\nCampaign completed.")


if __name__ == "__main__":
    main()
