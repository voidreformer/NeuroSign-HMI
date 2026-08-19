import os
import json
import time
import logging
import warnings
from collections import deque
from typing import Optional, Tuple, List

import numpy as np

try:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter
    load_delegate = getattr(getattr(tf, 'lite', None), 'experimental', None)
    if load_delegate:
        load_delegate = getattr(load_delegate, 'load_delegate', None)
except ImportError:
    try:
        import tflite_runtime.interpreter as tflite  # type: ignore[import-not-found,import-untyped]
        Interpreter = tflite.Interpreter
        load_delegate = getattr(tflite, 'load_delegate', None)
    except (ImportError, AttributeError):
        Interpreter = None
        load_delegate = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GestureClassifier:
    """
    Real-time gesture classifier using LSTM model on Arduino UNO Q with Qualcomm Adreno 702 GPU.

    Attributes:
        model_path (str): Path to the TFLite model file (gesture_lstm_int8.tflite).
        labels_path (str): Path to the labels JSON file.
        sequence_length (int): Number of frames per inference window (default: 30).
        confidence_threshold (float): Minimum confidence for valid classification (default: 0.85).
        input_shape (tuple): Expected model input shape (batch, sequence, features).
        labels (List[str]): Loaded gesture label names.
        interpreter (Interpreter): TFLite interpreter instance.
        input_details (list): Model input tensor details.
        output_details (list): Model output tensor details.
        buffer (deque): Circular buffer storing landmark sequences.
    """

    def __init__(
        self,
        model_path: str = "gesture_lstm_int8.tflite",
        labels_path: str = "labels.json",
        sequence_length: int = 30,
        confidence_threshold: float = 0.85,
        use_gpu_delegate: bool = True
    ) -> None:
        """
        Initialize the gesture classifier.

        Args:
            model_path: Path to the quantized TFLite model.
            labels_path: Path to the labels JSON file.
            sequence_length: Number of frames in the input sequence.
            confidence_threshold: Minimum confidence for positive classification.
            use_gpu_delegate: Attempt to load Qualcomm QNN GPU delegate.

        Raises:
            FileNotFoundError: If model or labels file not found.
            RuntimeError: If model loading or delegate initialization fails.
        """
        self.model_path = model_path
        self.labels_path = labels_path
        self.sequence_length = sequence_length
        self.confidence_threshold = confidence_threshold
        self.buffer = deque(maxlen=sequence_length)

        self._load_labels()
        self._load_model(use_gpu_delegate)
        self._validate_model()

        logger.info(
            "GestureClassifier initialized: model=%s, labels=%d, seq_len=%d, threshold=%.2f",
            model_path, len(self.labels), sequence_length, confidence_threshold
        )

    def _load_labels(self) -> None:
        """Load gesture labels from JSON file."""
        if not os.path.exists(self.labels_path):
            raise FileNotFoundError(f"Labels file not found: {self.labels_path}")

        with open(self.labels_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.gesture_metadata = {}
        if isinstance(data, dict):
            if "gestures" in data and isinstance(data["gestures"], dict):
                self.labels = [data["gestures"][str(i)]["label"] if isinstance(data["gestures"][str(i)], dict) else data["gestures"][str(i)] for i in range(len(data["gestures"]))]
                self.gesture_metadata = data["gestures"]
            elif "gestures" in data and isinstance(data["gestures"], list):
                self.labels = data["gestures"]
            elif "labels" in data and isinstance(data["labels"], dict):
                self.labels = [data["labels"][str(i)] for i in range(len(data["labels"]))]
            elif "labels" in data and isinstance(data["labels"], list):
                self.labels = data["labels"]
            else:
                self.labels = [data[str(i)] for i in range(len(data))]
        elif isinstance(data, list):
            self.labels = data
        else:
            raise ValueError("labels.json must be a list or dict mapping indices to labels")

        logger.debug("Loaded %d labels: %s", len(self.labels), self.labels)

    def _load_model(self, use_gpu_delegate: bool) -> None:
        """
        Load TFLite model with optional Qualcomm QNN GPU delegate.

        Args:
            use_gpu_delegate: Whether to attempt GPU delegate loading.
        """
        delegates = []

        if use_gpu_delegate:
            delegate_path = "libQnnTFLiteDelegate.so"
            if os.path.exists(delegate_path):
                try:
                    delegate = load_delegate(delegate_path)
                    delegates.append(delegate)
                    logger.info("Loaded Qualcomm QNN GPU delegate: %s", delegate_path)
                except Exception as e:
                    logger.warning("Failed to load GPU delegate %s: %s. Falling back to CPU.", delegate_path, e)
                    warnings.warn(f"GPU delegate unavailable: {e}. Using CPU inference.")
            else:
                logger.warning("GPU delegate not found at %s. Using CPU.", delegate_path)
                warnings.warn("Qualcomm QNN delegate (libQnnTFLiteDelegate.so) not found. Using CPU inference.")

        if Interpreter is None:
            raise ImportError("Neither tflite-runtime nor tensorflow is installed on this environment.")

        try:
            kwargs = {"model_path": self.model_path}
            if delegates:
                kwargs["experimental_delegates"] = delegates
            self.interpreter = Interpreter(**kwargs)
            self.interpreter.allocate_tensors()
        except Exception as e:
            raise RuntimeError(f"Failed to load TFLite model: {e}") from e

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        logger.debug("Input details: %s", self.input_details)
        logger.debug("Output details: %s", self.output_details)

    def _validate_model(self) -> None:
        """Validate model input/output shapes match expectations."""
        if len(self.input_details) != 1:
            raise ValueError(f"Expected 1 input tensor, got {len(self.input_details)}")

        input_shape = self.input_details[0]["shape"]
        expected_shape = (1, self.sequence_length, 63)

        if list(input_shape) != list(expected_shape):
            logger.warning(
                "Model input shape %s does not match expected %s. "
                "Ensure model expects (batch=1, seq_len=%d, features=63).",
                input_shape, expected_shape, self.sequence_length
            )

        if len(self.output_details) != 1:
            raise ValueError(f"Expected 1 output tensor, got {len(self.output_details)}")

        output_shape = self.output_details[0]["shape"]
        if output_shape[-1] != len(self.labels):
            raise ValueError(
                f"Model output classes ({output_shape[-1]}) != label count ({len(self.labels)})"
            )

    def update(self, landmarks: np.ndarray) -> None:
        """
        Add a new landmark frame to the circular buffer.

        Args:
            landmarks: Landmark vector of shape (63,) or (1, 63), dtype float32.

        Raises:
            ValueError: If landmarks shape is invalid.
        """
        if landmarks.ndim == 2 and landmarks.shape[0] == 1:
            landmarks = landmarks.squeeze(0)

        if landmarks.shape != (63,):
            raise ValueError(f"Expected landmarks shape (63,), got {landmarks.shape}")

        if landmarks.dtype != np.float32:
            landmarks = landmarks.astype(np.float32)

        self.buffer.append(landmarks)

    def classify(self) -> Optional[Tuple[str, float]]:
        """
        Run inference on the current buffer if full.

        Returns:
            Tuple of (gesture_label, confidence) if buffer full and confidence > threshold.
            None if buffer not full or confidence below threshold.

        Logs:
            Inference latency in milliseconds.
        """
        if len(self.buffer) < self.sequence_length:
            return None

        input_data = np.array(self.buffer, dtype=np.float32).reshape(1, self.sequence_length, 63)

        start_time = time.perf_counter()
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]["index"])
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.debug("Inference latency: %.2f ms", latency_ms)

        if latency_ms > 15.0:
            logger.warning("Inference latency %.2f ms exceeds 15 ms target", latency_ms)

        probabilities = output_data[0]
        predicted_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_idx])

        if confidence >= self.confidence_threshold:
            label = self.labels[predicted_idx]
            logger.info("Classified: %s (confidence=%.4f, latency=%.2f ms)", label, confidence, latency_ms)
            return label, confidence

        logger.debug("Max confidence %.4f below threshold %.2f", confidence, self.confidence_threshold)
        return None

    def reset(self) -> None:
        """Clear the landmark buffer."""
        self.buffer.clear()
        logger.debug("Buffer cleared")


if __name__ == "__main__":
    import sys

    print("=== GestureClassifier Self-Test ===")

    if not os.path.exists("gesture_lstm_int8.tflite"):
        print("Creating dummy model and labels for testing...")
        import subprocess
        result = subprocess.run([
            sys.executable, "-c", """
import numpy as np
import tensorflow as tf

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(30, 63)),
    tf.keras.layers.LSTM(32, return_sequences=False),
    tf.keras.layers.Dense(5, activation='softmax')
])
model.compile(optimizer='adam', loss='categorical_crossentropy')
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()
with open('gesture_lstm_int8.tflite', 'wb') as f:
    f.write(tflite_model)
print('Dummy model created')
"""
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to create dummy model: {result.stderr}")
            sys.exit(1)

    if not os.path.exists("labels.json"):
        labels = ["swipe_left", "swipe_right", "swipe_up", "swipe_down", "tap"]
        with open("labels.json", "w") as f:
            json.dump(labels, f)
        print("Created labels.json")

    try:
        classifier = GestureClassifier(
            model_path="gesture_lstm_int8.tflite",
            labels_path="labels.json",
            sequence_length=30,
            confidence_threshold=0.85,
            use_gpu_delegate=True
        )
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)

    print("\nFeeding synthetic landmark data...")
    np.random.seed(42)
    for i in range(35):
        landmarks = np.random.randn(63).astype(np.float32) * 0.1
        classifier.update(landmarks)

        if i >= 29:
            result = classifier.classify()
            if result:
                label, conf = result
                print(f"Frame {i+1}: {label} (confidence={conf:.4f})")
            else:
                print(f"Frame {i+1}: No classification (low confidence or buffer not ready)")

    print("\nTest complete.")