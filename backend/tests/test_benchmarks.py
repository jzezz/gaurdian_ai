import io

from benchmarks.run import BenchmarkRunner
from app.services.fusion_engine import FusionEngine


class FakeImageService:
    def moderate(self, _image):
        return {
            "nsfw_score": 0.1,
            "violence_score": 0.0,
            "weapon_score": 0.0,
            "hate_symbol_score": 0.0,
            "drugs_score": 0.0,
        }


class FakeTextService:
    def moderate(self, _text):
        return {
            "toxic": 0.0,
            "threat": 0.0,
            "harassment": 0.0,
            "profanity": 0.0,
            "adult_promo": 0.0,
        }


class FakeBaseline:
    def is_flagged(self, _image):
        return True

    def risk(self, _image):
        return 0.5


def test_benign_folder_samples_are_counted_as_false_positives():
    runner = BenchmarkRunner.__new__(BenchmarkRunner)
    runner.threshold = 0.4
    runner.image_service = FakeImageService()
    runner.text_service = FakeTextService()
    runner.fusion = FusionEngine()
    runner.baseline = FakeBaseline()

    result = runner.benchmark_image_false_positives({"benign": [("benign", io.BytesIO(b"sample"))]})

    assert result["samples"] == 1
    assert result["baseline_fp_rate"] == 1.0
    assert result["guardian_fp_rate"] == 0.0
    assert result["fp_reduction_pct"] == 100.0
