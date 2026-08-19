"""
NeuroSign-HMI: Wearable Glove Hub UART / Serial Bridge
Asynchronously receives real-time JSON telemetry from the TX Glove & ESP32-S3 Medical Hub
(Flex sensors, ADXL345 Pitch/Roll, Tremor/Spasm anomaly flags, and Vitals)
and dispatches events into the master orchestrator.
"""

import json
import time
import queue
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger("WearableBridge")

# Gesture ID mapping from ESP32-S3 Medical Hub
GLOVE_GESTURE_MAP = {
    1: "Water Please",
    2: "Food / Hungry",
    3: "Medicine / Painkiller",
    4: "Emergency - Need Help",
    5: "Turn On Room Light",
    6: "Turn Off Room Light",
    7: "Turn On Fan",
    8: "Turn Off Fan",
    9: "Severe Pain",
    10: "Time to Sleep",
    11: "Need Washroom",
    12: "Call Family",
    13: "Thank You",
    14: "Yes",
    15: "No"
}

class WearableGloveBridge:
    """
    Connects to the Wearable Hub serial interface and streams real-time biometric telemetry.
    """
    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        gesture_callback: Optional[Callable[[str, float], None]] = None,
        spasm_callback: Optional[Callable[[dict], None]] = None,
        sensor_callback: Optional[Callable[[dict], None]] = None
    ):
        self.port = port
        self.baudrate = baudrate
        self.gesture_callback = gesture_callback
        self.spasm_callback = spasm_callback
        self.sensor_callback = sensor_callback

        self.running = False
        self.is_connected = False
        self._thread: Optional[threading.Thread] = None
        self._serial_handle = None

    def start(self):
        """Starts background worker thread listening for serial packets."""
        self.running = True
        self._thread = threading.Thread(target=self._reader_worker, daemon=True)
        self._thread.start()
        logger.info(f"Wearable Glove Bridge started on port: {self.port} @ {self.baudrate} baud")

    def _reader_worker(self):
        """Background thread reading lines of JSON telemetry from the ESP32-S3 / UNO Q port."""
        try:
            import serial
            while self.running:
                try:
                    if self._serial_handle is None or not self._serial_handle.is_open:
                        self._serial_handle = serial.Serial(self.port, self.baudrate, timeout=1.0)
                        self.is_connected = True
                        logger.info(f"Connected to Wearable Glove Hub on {self.port}")

                    line = self._serial_handle.readline().decode('utf-8', errors='ignore').strip()
                    if line and line.startswith('{') and line.endswith('}'):
                        self._parse_packet(line)

                except (serial.SerialException, OSError) as e:
                    self.is_connected = False
                    if self._serial_handle and self._serial_handle.is_open:
                        self._serial_handle.close()
                    self._serial_handle = None
                    time.sleep(2.0)  # Retry connection
        except ImportError:
            logger.warning("pyserial not installed. Wearable Glove Bridge running in virtual simulation mode.")
            self._virtual_simulation_loop()

    def _virtual_simulation_loop(self):
        """Fallback simulation mode when no physical serial port is attached."""
        while self.running:
            time.sleep(1.0)

    def _parse_packet(self, raw_json: str):
        """Parses decoded JSON packet and dispatches callbacks."""
        try:
            data = json.loads(raw_json)

            # 1. Spasm / Tremor Anomaly Detection
            is_tremor = data.get("trm", 0)
            if is_tremor == 1 and self.spasm_callback:
                self.spasm_callback({
                    "type": "SPASM_ALERT",
                    "pitch": data.get("p", 0),
                    "roll": data.get("r", 0),
                    "timestamp": time.time()
                })

            # 2. Glove Gesture Trigger
            gid = data.get("gid", 0)
            conf = data.get("conf", 0.0)
            if gid in GLOVE_GESTURE_MAP and conf >= 0.80 and self.gesture_callback:
                gesture_label = GLOVE_GESTURE_MAP[gid]
                self.gesture_callback(gesture_label, conf)

            # 3. Vital Environmental Readings
            if self.sensor_callback:
                self.sensor_callback({
                    "temperature": data.get("temp", 0.0),
                    "humidity": data.get("hum", 0.0),
                    "pressure": data.get("press", 0.0),
                    "voc": data.get("voc", 0),
                    "voltage": data.get("v", 0.0),
                    "current_ma": data.get("ma", 0.0),
                    "battery": data.get("bat", 100),
                    "flex": [data.get("f1", 0), data.get("f2", 0), data.get("f3", 0)],
                    "source": "wearable_glove"
                })

        except json.JSONDecodeError:
            pass

    def stop(self):
        """Stops bridge and cleans up handles."""
        self.running = False
        if self._serial_handle and self._serial_handle.is_open:
            self._serial_handle.close()
