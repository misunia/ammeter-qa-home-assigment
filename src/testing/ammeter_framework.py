from __future__ import annotations

import time
import uuid
import json
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Dict, Any, List, Optional, Callable

from src.utils.config import load_config


MeasurementFn = Callable[[int, bytes], float]


class AmmeterTestFramework:
    def __init__(self, config_path: str = "config/config.yaml", results_dir: str = "results"):
        self.config = load_config(config_path)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def run_test(
        self,
        ammeter_type: str,
        get_measurement: MeasurementFn,
        *,
        measurements_count: Optional[int] = None,
        total_duration_seconds: Optional[float] = None,
        sampling_frequency_hz: Optional[float] = None,
        save: bool = True,
    ) -> Dict[str, Any]:
        """
        Run a sampling session for a given ammeter type and return result dict.
        """
        am_cfg = self._get_ammeter_cfg(ammeter_type)
        port = int(am_cfg["port"])
        command = am_cfg["command"].encode("utf-8") if isinstance(am_cfg["command"], str) else am_cfg["command"]

        sampling_defaults = (self.config.get("testing", {})
                               .get("sampling", {}))

        def pick(name, current):
            return current if current is not None else sampling_defaults.get(name)

        measurements_count = pick("measurements_count", measurements_count)
        total_duration_seconds = pick("total_duration_seconds", total_duration_seconds)
        sampling_frequency_hz = pick("sampling_frequency_hz", sampling_frequency_hz)

        self._validate_sampling_args(
            measurements_count=measurements_count,
            total_duration_seconds=total_duration_seconds,
            sampling_frequency_hz=sampling_frequency_hz,
        )

        run_id = str(uuid.uuid4())
        started_at = time.time()

        measurements, timestamps = self._sample(
            port=port,
            command=command,
            get_measurement=get_measurement,
            measurements_count=measurements_count,
            total_duration_seconds=total_duration_seconds,
            sampling_frequency_hz=sampling_frequency_hz,
        )

        stats = self._summarize(measurements)

        result: Dict[str, Any] = {
            "run_id": run_id,
            "started_at_epoch": started_at,
            "ammeter_type": ammeter_type,
            "ammeter": {
                "port": port,
                "command": command.decode(errors="replace"),
            },
            "sampling": {
                "measurements_count": measurements_count,
                "total_duration_seconds": total_duration_seconds,
                "sampling_frequency_hz": sampling_frequency_hz,
            },
            "data": {
                "measurements": measurements,
                "timestamps_epoch": timestamps,
            },
            "stats": stats,
        }

        if save:
            self._save_result(result)

        return result

    # -------- internal helpers --------

    def _get_ammeter_cfg(self, ammeter_type: str) -> Dict[str, Any]:
        try:
            return self.config["ammeters"][ammeter_type]
        except KeyError as e:
            available = ", ".join(sorted(self.config.get("ammeters", {}).keys()))
            raise KeyError(f"Unknown ammeter_type={ammeter_type!r}. Available: {available}")

    def _validate_sampling_args(
        self,
        *,
        measurements_count: Optional[int],
        total_duration_seconds: Optional[float],
        sampling_frequency_hz: Optional[float],
    ) -> None:
        if measurements_count is not None:
            if measurements_count <= 0:
                raise ValueError("measurements_count must be > 0")
            return

        if total_duration_seconds is None or sampling_frequency_hz is None:
            raise ValueError("Provide measurements_count OR (total_duration_seconds + sampling_frequency_hz)")

        if total_duration_seconds <= 0:
            raise ValueError("total_duration_seconds must be > 0")
        if sampling_frequency_hz <= 0:
            raise ValueError("sampling_frequency_hz must be > 0")

    def _sample(
        self,
        *,
        port: int,
        command: bytes,
        get_measurement: MeasurementFn,
        measurements_count: Optional[int],
        total_duration_seconds: Optional[float],
        sampling_frequency_hz: Optional[float],
    ) -> tuple[List[float], List[float]]:
        measurements: List[float] = []
        timestamps: List[float] = []

        def take_one() -> None:
            ts = time.time()
            val = float(get_measurement(port, command))
            timestamps.append(ts)
            measurements.append(val)

        if measurements_count is not None:
            for _ in range(measurements_count):
                take_one()
            return measurements, timestamps

        period = 1.0 / float(sampling_frequency_hz)
        end_time = time.time() + float(total_duration_seconds)

        while time.time() < end_time:
            t0 = time.time()
            take_one()

            # best-effort cadence (not real-time, but stable enough)
            elapsed = time.time() - t0
            sleep_for = period - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

        return measurements, timestamps

    def _summarize(self, values: List[float]) -> Dict[str, float]:
        if not values:
            raise ValueError("No measurements collected")

        return {
            "mean": float(mean(values)),
            "median": float(median(values)),
            "std": float(pstdev(values)),
            "min": float(min(values)),
            "max": float(max(values)),
        }

    def _save_result(self, result: Dict[str, Any]) -> Path:
        out_file = self.results_dir / f"{result['run_id']}.json"
        out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return out_file