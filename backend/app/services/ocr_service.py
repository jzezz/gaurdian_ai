import warnings
warnings.filterwarnings("ignore")

import io
from PIL import Image
import numpy as np

class OCRService:
    def __init__(self):
        self.reader = None
        self._load_model()

    def _load_model(self):
        try:
            import easyocr
            # English only for v1
            self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        except Exception as e:
            print(f"Warning: Could not load OCR model: {e}")
            self.reader = None

    def extract_text(self, image_bytes: io.BytesIO) -> str:
        if self.reader is None:
            return ""

        try:
            image = Image.open(image_bytes).convert("RGB")
            img_array = np.array(image)
            result = self.reader.readtext(img_array, detail=0)
            return " ".join(result) if result else ""
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
