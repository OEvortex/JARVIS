from typing import Tuple
import librosa
import numpy as np
from config import SAMPLE_RATE, N_MFCC

from types_sr import AudioProcessor, FeatureData, AudioData

class FeatureExtractor(AudioProcessor):
    @staticmethod
    def extract_features(audio_data: AudioData) -> FeatureData:
        try:
            mfccs: np.ndarray = librosa.feature.mfcc(
                y=audio_data, 
                sr=SAMPLE_RATE, 
                n_mfcc=N_MFCC
            )
            mfccs_scaled: FeatureData = np.mean(mfccs.T, axis=0)
            return mfccs_scaled
        except Exception as e:
            raise ValueError(f"Feature extraction failed: {str(e)}")

    @staticmethod
    def load_and_extract(file_path: str) -> FeatureData:
        try:
            audio, _ = librosa.load(file_path, sr=SAMPLE_RATE, res_type='kaiser_fast')
            return FeatureExtractor.extract_features(audio)
        except Exception as e:
            raise ValueError(f"Failed to load audio file {file_path}: {str(e)}")
