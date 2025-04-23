from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from deepface import DeepFace


@dataclass
class FaceRegion:
    x: int
    y: int
    width: int
    height: int


@dataclass
class FaceAnalysis:
    region: FaceRegion
    dominant_emotion: str
    emotions: Dict[str, float]


class RealtimeFaceAnalyzer:
    def __init__(
        self,
        camera_index: int = 0,
        window_name: str = "Real-time Face and Emotion Detection"
    ) -> None:
        """Initialize the real-time face analyzer.

        Args:
            camera_index: Index of the camera to use (default: 0)
            window_name: Name of the display window
        """
        self.camera_index = camera_index
        self.window_name = window_name
        self.capture: Optional[cv2.VideoCapture] = None
        self.text_color: Tuple[int, int, int] = (0, 255, 0)  # Green
        self.box_color: Tuple[int, int, int] = (0, 255, 0)  # Green
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.7
        self.line_thickness = 2

    def initialize_camera(self) -> bool:
        """Initialize the camera capture.

        Returns:
            bool: True if camera initialized successfully, False otherwise
        """
        self.capture = cv2.VideoCapture(self.camera_index)
        if not self.capture.isOpened():
            print("Error: Could not open camera.")
            return False
        return True

    def analyze_frame(self, frame: np.ndarray) -> List[FaceAnalysis]:
        """Analyze faces and emotions in a frame.

        Args:
            frame: Input frame from camera

        Returns:
            List of FaceAnalysis objects containing detection results
        """
        try:
            analysis = DeepFace.analyze(
                frame,
                actions=['emotion'],
                enforce_detection=False
            )
            
            results: List[FaceAnalysis] = []
            if analysis and len(analysis) > 0:
                for face in analysis:
                    region = FaceRegion(
                        x=face['region']['x'],
                        y=face['region']['y'],
                        width=face['region']['w'],
                        height=face['region']['h']
                    )
                    results.append(FaceAnalysis(
                        region=region,
                        dominant_emotion=face['dominant_emotion'],
                        emotions=face['emotion']
                    ))
            return results
        
        except Exception as e:
            print(f"Error during analysis: {e}")
            return []

    def draw_results(self, frame: np.ndarray, analysis: List[FaceAnalysis]) -> np.ndarray:
        """Draw detection results on the frame.

        Args:
            frame: Input frame
            analysis: List of face analysis results

        Returns:
            Frame with annotations
        """
        for face in analysis:
            # Draw rectangle around face
            cv2.rectangle(
                frame,
                (face.region.x, face.region.y),
                (face.region.x + face.region.width, face.region.y + face.region.height),
                self.box_color,
                self.line_thickness
            )
            
            # Draw emotion label
            cv2.putText(
                frame,
                face.dominant_emotion,
                (face.region.x, face.region.y - 10),
                self.font,
                self.font_scale,
                self.text_color,
                self.line_thickness
            )
        
        return frame

    def run(self) -> None:
        """Run the real-time face analysis loop."""
        if not self.initialize_camera():
            return

        while True:
            ret, frame = self.capture.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            # Analyze frame and draw results
            analysis_results = self.analyze_frame(frame)
            annotated_frame = self.draw_results(frame, analysis_results)

            # Display the result
            cv2.imshow(self.window_name, annotated_frame)

            # Check for quit command
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.capture is not None:
            self.capture.release()
        cv2.destroyAllWindows()


def main() -> None:
    """Main function to run the real-time face analyzer."""
    analyzer = RealtimeFaceAnalyzer()
    analyzer.run()


if __name__ == "__main__":
    main()