import cv2
from modules.hand_detector import HandDetector
from modules.gesture_recognizer import GestureRecognizer
from modules.mouse_controller import MouseController
from config.settings import *

def main():
    # Initialize objects
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(3, CAMERA_WIDTH)
    cap.set(4, CAMERA_HEIGHT)
    
    detector = HandDetector(
        max_hands=MAX_HANDS,
        detection_confidence=DETECTION_CONFIDENCE,
        tracking_confidence=TRACKING_CONFIDENCE
    )
    
    gesture_recognizer = GestureRecognizer()
    mouse_controller = MouseController(
        smoothing=SMOOTHING_FACTOR,
        screen_size=SCREEN_RESOLUTION
    )

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Flip frame horizontally for natural movement
        frame = cv2.flip(frame, 1)
        
        # Detect hands
        frame, hand_landmarks = detector.find_hands(frame)
        
        if hand_landmarks:
            # Get landmark positions
            positions = detector.get_landmark_position(frame)
            if positions:
                # Get index finger tip position for cursor control
                index_finger_tip = positions[8]
                
                # Move cursor
                mouse_controller.move_cursor(
                    (index_finger_tip[1], index_finger_tip[2]),
                    (CAMERA_WIDTH, CAMERA_HEIGHT)
                )
                
                # Recognize and perform gesture
                gesture = gesture_recognizer.recognize_gesture(positions)
                mouse_controller.perform_action(gesture)

        # Display
        cv2.imshow("Gesture Control", frame)
        
        # Exit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
