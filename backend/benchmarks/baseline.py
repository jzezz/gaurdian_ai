"""Single-model baseline used to quantify false-positive reduction.

The baseline is a naive NSFW-only detector: it makes a decision based solely
on the CLIP 'explicit sexual content' score with no context awareness and no
text/OCR fusion. Guardian AI (the full pipeline) should achieve fewer false
positives on benign content than this baseline — that delta is the
'false positive reduction' figure on the resume.
"""

import io
from typing import Dict

from PIL import Image


class SingleModelBaseline:
    """Wraps the CLIP image classifier as a binary NSFW-only detector."""

    def __init__(self, image_service, threshold: float = 0.5):
        self.image_service = image_service
        self.threshold = threshold

    def is_flagged(self, image_bytes: io.BytesIO) -> bool:
        result = self.image_service.moderate(image_bytes, context_aware=False)
        # Naive baseline: NSFW score alone decides, no medical/artistic context
        return result["nsfw_score"] >= self.threshold

    def risk(self, image_bytes: io.BytesIO) -> float:
        return self.image_service.moderate(image_bytes, context_aware=False)["nsfw_score"]
