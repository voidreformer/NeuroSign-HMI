"""
NeuroSign-HMI Max: Inter-Processor Communication (IPC) Bridge
Manages low-overhead MessagePack RPC over /var/run/arduino-router.sock
connecting the Qualcomm Dragonwing MPU (Linux) and STM32U585 MCU (Zephyr RTOS).
"""

import time
import logging
import threading
from typing import Callable, Dict, Any, Optional

try:
    from arduino.app_utils import Bridge
except ImportError:
    # Fallback / Mock Bridge for development & testing outside Arduino App Lab
    class MockBridge:
        @staticmethod
        def begin():
            logging.info("[MOCK IPC] Bridge connection initialized.")

        @staticmethod
        def provide(name: str, callback: Callable):
            logging.info(f"[MOCK IPC] Registered provider for '{name}'")

        @staticmethod
        def call(name: str, *args) -> Any:
            logging.info(f"[MOCK IPC] Invoking '{name}' with args: {args}")
            return True

        @staticmethod
        def notify(name: str, *args):
            logging.info(f"[MOCK IPC] Notification '{name}' sent with args: {args}")

    Bridge = MockBridge

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IPC_Bridge")


class IPCBridgeManager:
    """
    Thread-safe IPC Bridge Manager for the Arduino UNO Q dual-brain architecture.
    """
    _instance: Optional['IPCBridgeManager'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(IPCBridgeManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.callbacks: Dict[str, list[Callable]] = {
            "radar_presence": [],
            "sensor_telemetry": [],
            "joystick_event": []
        }
        self._init_bridge()

    def _init_bridge(self):
        """Initializes the Unix domain socket connection to arduino-router."""
        try:
            Bridge.begin()
            logger.info("Connected to /var/run/arduino-router.sock successfully.")

            # Register incoming MCU telemetry streams
            Bridge.provide("radar_telemetry_event", self._on_radar_event)
            Bridge.provide("sensor_bus_event", self._on_sensor_event)
            Bridge.provide("joystick_telemetry_event", self._on_joystick_event)
        except Exception as e:
            logger.error(f"Failed to initialize Arduino Bridge: {e}")

    # ------------------ Inbound Telemetry Handlers ------------------

    def register_callback(self, event_name: str, callback: Callable):
        """Register a Python listener for incoming MCU telemetry."""
        if event_name in self.callbacks:
            self.callbacks[event_name].append(callback)
            logger.info(f"Registered listener for event: {event_name}")

    def _on_radar_event(self, presence_state: int, distance_cm: int, energy: int):
        """Dispatched when HLK-LD2410C radar detects human presence."""
        payload = {
            "present": bool(presence_state),
            "distance_cm": distance_cm,
            "energy": energy,
            "timestamp": time.time()
        }
        for cb in self.callbacks["radar_presence"]:
            try:
                cb(payload)
            except Exception as ex:
                logger.error(f"Error in radar callback: {ex}")

    def _on_sensor_event(self, voc_index: int, bus_volts: float, current_ma: float, temp_c: float, humidity: float):
        """Dispatched when MCU aggregates SGP40, INA219, and DHT22 telemetry."""
        payload = {
            "voc_index": voc_index,
            "bus_volts": bus_volts,
            "current_ma": current_ma,
            "power_mw": bus_volts * current_ma,
            "temp_c": temp_c,
            "humidity": humidity,
            "timestamp": time.time()
        }
        for cb in self.callbacks["sensor_telemetry"]:
            try:
                cb(payload)
            except Exception as ex:
                logger.error(f"Error in sensor callback: {ex}")

    def _on_joystick_event(self, x: int, y: int, clicked: int):
        """Dispatched when Modulino Joystick state changes."""
        payload = {"x": x, "y": y, "clicked": bool(clicked)}
        for cb in self.callbacks["joystick_event"]:
            try:
                cb(payload)
            except Exception as ex:
                logger.error(f"Error in joystick callback: {ex}")

    # ------------------ Outbound Commands to MCU ------------------

    def trigger_relay(self, relay_id: int, state: bool) -> bool:
        """
        Actuates 5V/12V solid state relays via synchronous RPC.
        relay_id: 1 (Room Light), 2 (Emergency Alarm/Strobe)
        state: True (ON), False (OFF)
        """
        try:
            logger.info(f"[OUTBOUND] Triggering Relay {relay_id} -> {'ON' if state else 'OFF'}")
            return Bridge.call("mcu_set_relay", int(relay_id), int(state))
        except Exception as e:
            logger.error(f"Failed to trigger relay {relay_id}: {e}")
            return False

    def set_camera_pan_tilt(self, pan_angle: int, tilt_angle: int):
        """
        Commands the SG90 servos to dynamically track the user's hands.
        pan_angle: 0 to 180 degrees
        tilt_angle: 0 to 180 degrees
        """
        try:
            # Clamping bounds
            pan = max(0, min(180, int(pan_angle)))
            tilt = max(0, min(180, int(tilt_angle)))
            Bridge.notify("mcu_set_pan_tilt", pan, tilt)
        except Exception as e:
            logger.error(f"Failed to update pan/tilt servo angles: {e}")

    def send_emergency_sms(self, phone_number: str, message: str) -> bool:
        """
        Commands the SIM800C GSM module to transmit an offline SOS SMS.
        """
        try:
            logger.warning(f"[OUTBOUND SOS] Dispatching SMS to {phone_number}: {message}")
            return Bridge.call("mcu_send_sms", str(phone_number), str(message))
        except Exception as e:
            logger.error(f"Failed to send emergency SMS: {e}")
            return False

    def update_matrix_glyph(self, glyph_id: int):
        """
        Updates the 8x13 blue LED matrix with expressive iconography.
        glyph_id: 0 (IDLE), 1 (GESTURE_OK), 2 (EMERGENCY_SOS), 3 (SPEAKING), 4 (LISTENING)
        """
        try:
            Bridge.notify("mcu_set_glyph", int(glyph_id))
        except Exception as e:
            logger.error(f"Failed to update LED matrix glyph: {e}")
