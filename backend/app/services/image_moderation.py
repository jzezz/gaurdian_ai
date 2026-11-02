import warnings
warnings.filterwarnings("ignore")

from transformers import pipeline
from PIL import Image
import io

class ImageModerationService:
    def __init__(self):
        self.classifier = None
        self._load_model()

    def _load_model(self):
        try:
            # Use CLIP for zero-shot image classification
            self.classifier = pipeline(
                "zero-shot-image-classification",
                model="openai/clip-vit-base-patch32",
                device=-1  # CPU
            )
        except Exception as e:
            print(f"Warning: Could not load image model: {e}")
            self.classifier = None

    def moderate(self, image_bytes: io.BytesIO, context_aware: bool = True) -> dict:
        if self.classifier is None:
            return self._fallback_response()

        try:
            image = Image.open(image_bytes).convert("RGB")
            candidate_labels = [
                "explicit sexual content",
                "violence and gore",
                "weapons and firearms",
                "hate symbols and extremism",
                "drugs and substance abuse",
                "safe and appropriate content",
                "medical or educational content",
                "artistic or cultural content"
            ]

            results = self.classifier(image, candidate_labels=candidate_labels)
            scores = {r["label"]: r["score"] for r in results}

            # Map to our categories
            nsfw_score = scores.get("explicit sexual content", 0.0)
            violence_score = scores.get("violence and gore", 0.0)
            weapon_score = scores.get("weapons and firearms", 0.0)
            hate_score = scores.get("hate symbols and extremism", 0.0)
            drugs_score = scores.get("drugs and substance abuse", 0.0)
            safe_score = scores.get("safe and appropriate content", 0.0)
            medical_score = scores.get("medical or educational content", 0.0)
            artistic_score = scores.get("artistic or cultural content", 0.0)

            # Context-aware adjustments: if medical/artistic scores are high, reduce nsfw
            if context_aware and (medical_score > 0.3 or artistic_score > 0.3):
                nsfw_score = max(0.0, nsfw_score - 0.3)

            return {
                "nsfw_score": round(nsfw_score, 4),
                "violence_score": round(violence_score, 4),
                "weapon_score": round(weapon_score, 4),
                "hate_symbol_score": round(hate_score, 4),
                "drugs_score": round(drugs_score, 4),
                "safe_score": round(safe_score, 4),
                "medical_score": round(medical_score, 4),
                "artistic_score": round(artistic_score, 4),
            }
        except Exception as e:
            print(f"Image moderation error: {e}")
            return self._fallback_response()

    def _fallback_response(self) -> dict:
        return {
            "nsfw_score": 0.0,
            "violence_score": 0.0,
            "weapon_score": 0.0,
            "hate_symbol_score": 0.0,
            "drugs_score": 0.0,
            "safe_score": 1.0,
            "medical_score": 0.0,
            "artistic_score": 0.0,
        }
