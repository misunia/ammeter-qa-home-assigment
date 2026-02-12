import threading
import time

from Ammeters.Circutor_Ammeter import CircutorAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.client import request_current_from_ammeter


def run_greenlee_emulator():
    greenlee = GreenleeAmmeter(5000)
    greenlee.start_server()


def run_entes_emulator():
    entes = EntesAmmeter(5001)
    entes.start_server()


def run_circutor_emulator():
    circutor = CircutorAmmeter(5002)
    circutor.start_server()


if __name__ == "__main__":
    # Start each ammeter emulator in a separate thread
    threading.Thread(target=run_greenlee_emulator, daemon=True).start()
    threading.Thread(target=run_entes_emulator, daemon=True).start()
    threading.Thread(target=run_circutor_emulator, daemon=True).start()

    # Give servers time to start
    time.sleep(3)

    # --- OPTIONAL: manual smoke test (not the real tests) ---
    print("Smoke test:")
    print(request_current_from_ammeter(5000, b"MEASURE_GREENLEE -get_measurement"))
    print(request_current_from_ammeter(5001, b"MEASURE_ENTES -get_data"))
    print(request_current_from_ammeter(5002, b"MEASURE_CIRCUTOR -get_measurement -current"))

    # Keep process alive so pytest / framework can connect
    while True:
        time.sleep(1)