import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple


class LandmarkExtractor:
    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.6,
        model_complexity: int = 1,
        smoothing_alpha: float = 0.7,
    ):
        self._mp_hands = mp.solutions.hands
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_drawing_styles = mp.solutions.drawing_styles

        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity,
        )

        self._smoothing_alpha = smoothing_alpha
        self._prev_landmarks: Optional[np.ndarray] = None
        self._initialized = False

    def begin(self) -> bool:
        if self._initialized:
            return True
        try:
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            _ = self._hands.process(cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB))
            self._initialized = True
            return True
        except Exception:
            return False

    def process(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[Tuple[float, float]], np.ndarray]:
        if not self._initialized:
            self.begin()

        if frame is None or frame.size == 0:
            return None, None, frame

        annotated_frame = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self._hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        landmarks_flat: Optional[np.ndarray] = None
        hand_center: Optional[Tuple[float, float]] = None

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            self._mp_drawing.draw_landmarks(
                annotated_frame,
                hand_landmarks,
                self._mp_hands.HAND_CONNECTIONS,
                self._mp_drawing_styles.get_default_hand_landmarks_style(),
                self._mp_drawing_styles.get_default_hand_connections_style(),
            )

            h, w = frame.shape[:2]
            landmarks = np.array(
                [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark],
                dtype=np.float32,
            )

            wrist = landmarks[0:1]
            landmarks_normalized = landmarks - wrist

            if self._prev_landmarks is not None:
                landmarks_normalized = (
                    self._smoothing_alpha * landmarks_normalized
                    + (1.0 - self._smoothing_alpha) * self._prev_landmarks
                )

            self._prev_landmarks = landmarks_normalized.copy()
            landmarks_flat = landmarks_normalized.flatten()

            x_coords = landmarks[:, 0] * w
            y_coords = landmarks[:, 1] * h
            x_min, x_max = x_coords.min(), x_coords.max()
            y_min, y_max = y_coords.min(), y_coords.max()
            center_x = (x_min + x_max) / 2.0 / w
            center_y = (y_min + y_max) / 2.0 / h
            hand_center = (float(center_x), float(center_y))

        return landmarks_flat, hand_center, annotated_frame

    def close(self) -> None:
        if self._hands is not None:
            self._hands.close()
            self._hands = None
        self._initialized = False
        self._prev_landmarks = None


if __name__ == "__main__":
    import sys

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open camera", file=sys.stderr)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    extractor = LandmarkExtractor()
    if not extractor.begin():
        print("Failed to initialize MediaPipe Hands", file=sys.stderr)
        cap.release()
        sys.exit(1)

    print("LandmarkExtractor test running. Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            landmarks, center, annotated = extractor.process(frame)

            if landmarks is not None:
                print(f"Landmarks: {landmarks.shape}, Center: {center}")
            else:
                print("No hand detected")

            cv2.imshow("Hand Landmarks", annotated)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        extractor.close()
        cap.release()
        cv2.destroyAllWindows()