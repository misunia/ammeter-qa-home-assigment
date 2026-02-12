import threading
import time
import pytest
import yaml

from src.testing.ammeter_framework import AmmeterTestFramework
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.client import request_current_from_ammeter


AMMETERS = ["greenlee", "entes", "circutor"]


@pytest.fixture(scope="session", autouse=True)
def emulators():
    # Start emulators once for the whole test session
    threading.Thread(target=lambda: GreenleeAmmeter(5000).start_server(), daemon=True).start()
    threading.Thread(target=lambda: EntesAmmeter(5001).start_server(), daemon=True).start()
    threading.Thread(target=lambda: CircutorAmmeter(5002).start_server(), daemon=True).start()

    time.sleep(2)  # give servers time to boot


@pytest.fixture
def framework(tmp_path):
    return AmmeterTestFramework("config/config.yaml", results_dir=str(tmp_path / "results"))


@pytest.mark.parametrize("ammeter_type", AMMETERS)
def test_run_test_collects_measurements_and_stats(framework, ammeter_type):
    result = framework.run_test(
        ammeter_type,
        request_current_from_ammeter,
        measurements_count=5,
        save=True,
    )

    measurements = result["data"]["measurements"]
    assert len(measurements) == 5
    assert all(isinstance(x, (int, float)) for x in measurements)

    stats = result["stats"]
    for key in ("mean", "median", "std", "min", "max"):
        assert key in stats
        assert isinstance(stats[key], (int, float))


def test_missing_sampling_params_raises(tmp_path):
    cfg = {
        "testing": {"sampling": {"measurements_count": None, "total_duration_seconds": None, "sampling_frequency_hz": None}},
        "ammeters": {"greenlee": {"port": 5000, "command": "MEASURE_GREENLEE -get_measurement"}},
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")

    fw = AmmeterTestFramework(str(cfg_path), results_dir=str(tmp_path / "results"))

    with pytest.raises(ValueError):
        fw.run_test("greenlee", request_current_from_ammeter, save=False)

def test_partial_sampling_params_raise(tmp_path):
    cfg = {
        "testing": {"sampling": {"measurements_count": None, "total_duration_seconds": None, "sampling_frequency_hz": None}},
        "ammeters": {"greenlee": {"port": 5000, "command": "MEASURE_GREENLEE -get_measurement"}},
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")

    fw = AmmeterTestFramework(str(cfg_path), results_dir=str(tmp_path / "results"))

    with pytest.raises(ValueError):
        fw.run_test("greenlee", request_current_from_ammeter, total_duration_seconds=1, save=False)


def test_sampling_by_duration_and_frequency(framework):
    result = framework.run_test(
        "greenlee",
        request_current_from_ammeter,
        total_duration_seconds=1.0,
        sampling_frequency_hz=5.0,
        save=False,
    )

    measurements = result["data"]["measurements"]

    # Windows timing is not exact, so don't assert an exact number
    assert len(measurements) >= 3
