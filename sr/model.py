from typing import Optional, Tuple
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, LSTM
from types_sr import ModelInterface, FeatureData, ModelPrediction

class VoiceModel(ModelInterface):
    def __init__(self, input_shape: int) -> None:
        self.model: Sequential = self._build_model(input_shape)
        
    def _build_model(self, input_shape: int) -> Sequential:
        model = Sequential([
            Dense(512, activation='relu', input_shape=(input_shape,)),
            Dropout(0.4),
            Dense(256, activation='relu'),
            Dropout(0.3),
            Dense(128, activation='relu'),
            Dropout(0.2),
            Dense(64, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            loss='binary_crossentropy',
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            metrics=['accuracy']
        )
        return model

    def predict(self, features: FeatureData) -> ModelPrediction:
        prediction = self.model.predict(features, verbose=0)
        return float(prediction[0][0])

    def train(self, features: FeatureData, labels: np.ndarray, 
             epochs: int = 50, batch_size: int = 32) -> tf.keras.callbacks.History:
        return self.model.fit(
            features, labels,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=5,
                    restore_best_weights=True
                )
            ]
        )

    def save(self, path: str) -> None:
        self.model.save(path)

    @staticmethod
    def load(path: str) -> 'VoiceModel':
        model = load_model(path)
        voice_model = VoiceModel(model.input_shape[1])
        voice_model.model = model
        return voice_model
