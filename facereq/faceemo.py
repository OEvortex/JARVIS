import os
# Suppress TensorFlow logging messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # FATAL
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from jprinter import jp #pip install jprinter
import torch
from PIL import Image
from rich import print
from transformers import AutoImageProcessor, AutoModelForImageClassification
from transformers.modeling_outputs import ImageClassifierOutput


@dataclass
class EmotionPrediction:
    emotion: str
    confidence_scores: Dict[str, float]


class EmotionRecognizer:
    def __init__(self, model_name: str = "Abhaykoul/emo-face-rec") -> None:
        """Initialize the emotion recognizer with a pre-trained model.

        Args:
            model_name: The name or path of the pre-trained model
        """
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = AutoModelForImageClassification.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def load_image(self, image_path: str | Path) -> Image.Image:
        """Load an image from the specified path.

        Args:
            image_path: Path to the image file

        Returns:
            Loaded PIL Image
        """
        return Image.open(image_path)

    def predict(self, image: Image.Image) -> EmotionPrediction:
        """Predict emotion from the input image.

        Args:
            image: PIL Image to analyze

        Returns:
            EmotionPrediction containing the predicted emotion and confidence scores
        """
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs: ImageClassifierOutput = self.model(**inputs)

        predicted_class_id = outputs.logits.argmax(-1).item()
        predicted_emotion = self.model.config.id2label[predicted_class_id]

        confidence_scores = torch.nn.functional.softmax(outputs.logits, dim=-1)
        scores = {
            self.model.config.id2label[i]: score.item()
            for i, score in enumerate(confidence_scores[0])
        }

        return EmotionPrediction(emotion=predicted_emotion, confidence_scores=scores)

    def display_results(self, prediction: EmotionPrediction) -> None:
        """Display the prediction results.

        Args:
            prediction: EmotionPrediction containing results to display
        """
        jp(prediction.emotion)
        for emotion, score in prediction.confidence_scores.items():
            jp(f"{emotion}: {score:.4f}")


def main() -> None:
    """Main function to demonstrate the emotion recognition pipeline."""
    image_path = "image.png"
    
    recognizer = EmotionRecognizer()
    image = recognizer.load_image(image_path)
    prediction = recognizer.predict(image)
    recognizer.display_results(prediction)


if __name__ == "__main__":
    main()