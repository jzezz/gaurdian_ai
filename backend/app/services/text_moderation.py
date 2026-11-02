import warnings
warnings.filterwarnings("ignore")

from transformers import pipeline

class TextModerationService:
    def __init__(self):
        self.classifier = None
        self._load_model()

    def _load_model(self):
        try:
            # Use BART for zero-shot text classification
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU
            )
        except Exception as e:
            print(f"Warning: Could not load text model: {e}")
            self.classifier = None

    def moderate(self, text: str) -> dict:
        if self.classifier is None or not text.strip():
            return self._fallback_response()

        try:
            candidate_labels = [
                "toxicity and hate speech",
                "threats and violence",
                "harassment and bullying",
                "profanity and offensive language",
                "promotional adult content",
                "safe and neutral content"
            ]

            result = self.classifier(text, candidate_labels, multi_label=True)
            scores = {label: score for label, score in zip(result["labels"], result["scores"])}

            toxic = scores.get("toxicity and hate speech", 0.0)
            threat = scores.get("threats and violence", 0.0)
            harassment = scores.get("harassment and bullying", 0.0)
            profanity = scores.get("profanity and offensive language", 0.0)
            adult_promo = scores.get("promotional adult content", 0.0)
            safe = scores.get("safe and neutral content", 0.0)

            # Determine overall safety
            max_risk = max(toxic, threat, harassment, profanity, adult_promo)
            is_safe = max_risk < 0.3 and safe > 0.5

            return {
                "toxic": round(toxic, 4),
                "threat": round(threat, 4),
                "harassment": round(harassment, 4),
                "profanity": round(profanity, 4),
                "adult_promo": round(adult_promo, 4),
                "safe_score": round(safe, 4),
                "safe": is_safe,
                "confidence": round(max_risk if not is_safe else safe, 4),
            }
        except Exception as e:
            print(f"Text moderation error: {e}")
            return self._fallback_response()

    def _fallback_response(self) -> dict:
        return {
            "toxic": 0.0,
            "threat": 0.0,
            "harassment": 0.0,
            "profanity": 0.0,
            "adult_promo": 0.0,
            "safe_score": 1.0,
            "safe": True,
            "confidence": 0.0,
        }
