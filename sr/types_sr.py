from typing import TypeVar, Protocol, List, Dict, Optional, Union, Tuple
import numpy as np
import numpy.typing as npt

AudioData = npt.NDArray[np.float32]
FeatureData = npt.NDArray[np.float32]
ModelPrediction = float

class AudioProcessor(Protocol):
    def process_audio(self, audio_data: AudioData) -> FeatureData: ...

class ModelInterface(Protocol):
    def predict(self, features: FeatureData) -> ModelPrediction: ...
    def train(self, features: List[FeatureData], labels: List[int]) -> None: ...
