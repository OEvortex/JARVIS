import os
from typing import List, Tuple, Optional
import numpy as np
from sr.config import *
from sr.feature_extractor import FeatureExtractor
from sr.model import VoiceModel
from sr.realtime_classifier import RealtimeClassifier, AudioConfig
from sr.types_sr import FeatureData

class VoiceRecognitionSystem:
    def __init__(self) -> None:
        self.feature_extractor = FeatureExtractor()
        self.model: Optional[VoiceModel] = None
        self.features_array: Optional[np.ndarray] = None
        self.labels_array: Optional[np.ndarray] = None
        
    def load_training_data(self) -> Tuple[List[FeatureData], List[int]]:
        features: List[FeatureData] = []
        labels: List[int] = []
        
        # Load my voice samples
        for file in os.listdir(MY_VOICE_PATH):
            if file.endswith('.wav'):
                file_path = os.path.join(MY_VOICE_PATH, file)
                features.append(self.feature_extractor.load_and_extract(file_path))
                labels.append(1)

        # Load other voice samples
        for file in os.listdir(OTHER_VOICE_PATH):
            if file.endswith('.wav'):
                file_path = os.path.join(OTHER_VOICE_PATH, file)
                features.append(self.feature_extractor.load_and_extract(file_path))
                labels.append(0)
                
        return features, labels

    def prepare_training_data(self) -> None:
        try:
            features, labels = self.load_training_data()
            
            if not features:
                raise ValueError("No training data available")
                
            self.features_array = np.array(features)
            self.labels_array = np.array(labels)
            
        except Exception as e:
            print(f"Error preparing training data: {e}")
            raise

    def initialize_model(self) -> None:
        if os.path.exists(MODEL_PATH):
            print("Loading existing model...")
            self.model = VoiceModel.load(MODEL_PATH)
        else:
            print("Training new model...")
            self.prepare_training_data()
            
            if self.features_array is None or len(self.features_array.shape) < 2:
                raise ValueError("Features array is not properly initialized")
            
            self.model = VoiceModel(self.features_array.shape[1])
            self.model.train(self.features_array, self.labels_array)
            self.model.save(MODEL_PATH)

    def run(self) -> None:
        if self.model is None:
            raise ValueError("Model not initialized")
            
        classifier = RealtimeClassifier(
            model=self.model,
            feature_extractor=self.feature_extractor,
            threshold=0.5,
            audio_config=AudioConfig()
        )
        
        print("Starting real-time voice recognition...")
        print("Press Ctrl+C to stop")
        try:
            classifier.start_recording()
        except KeyboardInterrupt:
            classifier.stop_recording()
            print("\nStopped voice recognition")

def main() -> None:
    # Create data directories if they don't exist
    os.makedirs(MY_VOICE_PATH, exist_ok=True)
    os.makedirs(OTHER_VOICE_PATH, exist_ok=True)

    system = VoiceRecognitionSystem()
    try:
        system.initialize_model()
        system.run()
    except Exception as e:
        print(f"Error initializing system: {e}")

if __name__ == "__main__":
    main()
