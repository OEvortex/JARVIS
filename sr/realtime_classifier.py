from typing import Optional, Callable, Tuple, Dict, Any
import pyaudio
import numpy as np
import wave
import threading
from queue import Queue
from dataclasses import dataclass
from config import SAMPLE_RATE, DURATION
from feature_extractor import FeatureExtractor
from types_sr import AudioData, ModelInterface, ModelPrediction

@dataclass
class AudioConfig:
    format: int = pyaudio.paFloat32
    channels: int = 1
    rate: int = SAMPLE_RATE
    chunk: int = 1024
    
class RealtimeClassifier:
    def __init__(
        self, 
        model: ModelInterface,
        feature_extractor: FeatureExtractor,
        threshold: float = 0.5,
        audio_config: Optional[AudioConfig] = None
    ) -> None:
        self.model = model
        self.feature_extractor = feature_extractor
        self.threshold = threshold
        self.audio_config = audio_config or AudioConfig()
        self.audio_queue: Queue = Queue()
        self.is_running: bool = False
        self._callback_fn: Optional[Callable] = None

    def set_callback(self, callback_fn: Callable[[bool], None]) -> None:
        self._callback_fn = callback_fn
        
    def audio_callback(
        self, 
        in_data: bytes, 
        frame_count: int, 
        time_info: Dict, 
        status: int
    ) -> Tuple[bytes, int]:
        self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def process_audio(self, audio_data: AudioData) -> bool:
        try:
            features = self.feature_extractor.extract_features(audio_data)
            features = np.expand_dims(features, axis=0)
            prediction = self.model.predict(features)
            return prediction > self.threshold
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            return False

    def start_recording(self) -> None:
        self.is_running = True
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=self.audio_config.format,
                channels=self.audio_config.channels,
                rate=self.audio_config.rate,
                input=True,
                frames_per_buffer=self.audio_config.chunk,
                stream_callback=self.audio_callback
            )
            
            stream.start_stream()
            
            while self.is_running:
                if not self.audio_queue.empty():
                    audio_data = np.frombuffer(
                        self.audio_queue.get(), 
                        dtype=np.float32
                    )
                    is_my_voice = self.process_audio(audio_data)
                    
                    if self._callback_fn:
                        self._callback_fn(is_my_voice)
                    else:
                        print("✓ Your voice detected!" if is_my_voice else "✗ Unknown voice")
                        
        except Exception as e:
            print(f"Error in audio stream: {str(e)}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def stop_recording(self) -> None:
        self.is_running = False
