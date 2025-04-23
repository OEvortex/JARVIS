import numpy as np
from time import time

class GestureRecognizer:
    def __init__(self):
        self.prev_positions = []
        self.gesture_history = []
        self.last_gesture_time = time()

    def recognize_gesture(self, landmarks):
        if not landmarks:
            return "NONE"

        # Extract finger states
        thumb = self._is_thumb_up(landmarks)
        index = self._is_finger_extended(landmarks, 8)
        middle = self._is_finger_extended(landmarks, 12)
        ring = self._is_finger_extended(landmarks, 16)
        pinky = self._is_finger_extended(landmarks, 20)

        # Calculate hand orientation
        palm_direction = self._get_palm_direction(landmarks)
        
        # Recognize gestures
        current_time = time()
        gesture = "NONE"

        if thumb and index and not middle and not ring and not pinky:
            gesture = "DRAG"
        elif index and not middle and not ring and not pinky:
            gesture = "LEFT_CLICK"
        elif index and middle and not ring and not pinky:
            gesture = "RIGHT_CLICK"
        elif all([index, middle, ring, pinky]):
            if palm_direction == "UP":
                gesture = "VOLUME_UP"
            elif palm_direction == "DOWN":
                gesture = "VOLUME_DOWN"
            else:
                gesture = "MOVE"
        elif index and middle and ring and not pinky:
            if palm_direction == "UP":
                gesture = "BRIGHTNESS_UP"
            elif palm_direction == "DOWN":
                gesture = "BRIGHTNESS_DOWN"
            else:
                gesture = "SCROLL"
        elif all([thumb, index, middle, ring, pinky]):
            gesture = "SCREENSHOT"
        
        # Track gesture history
        if current_time - self.last_gesture_time > 0.5:
            self.gesture_history.append((gesture, current_time))
            self.last_gesture_time = current_time
            
            # Detect double click
            if self._is_double_click(gesture):
                gesture = "DOUBLE_CLICK"

        # Keep only recent gesture history
        self.gesture_history = [(g, t) for g, t in self.gesture_history 
                              if current_time - t < 2.0]
        
        return gesture

    def _get_palm_direction(self, landmarks):
        wrist = landmarks[0]
        middle_base = landmarks[9]
        
        # Calculate vertical direction
        if middle_base[2] < wrist[2]:
            return "UP"
        elif middle_base[2] > wrist[2]:
            return "DOWN"
        return "NEUTRAL"

    def _is_double_click(self, current_gesture):
        if current_gesture != "LEFT_CLICK":
            return False
            
        click_times = [t for g, t in self.gesture_history[-3:] 
                      if g == "LEFT_CLICK"]
        
        if len(click_times) >= 2:
            return click_times[-1] - click_times[-2] < 0.5
            
        return False

    def _is_thumb_up(self, landmarks):
        thumb_tip = landmarks[4]
        thumb_base = landmarks[2]
        return thumb_tip[2] < thumb_base[2]

    def _is_finger_extended(self, landmarks, finger_tip_idx):
        finger_tip = landmarks[finger_tip_idx]
        finger_base = landmarks[finger_tip_idx - 2]
        return finger_tip[2] < finger_base[2]
