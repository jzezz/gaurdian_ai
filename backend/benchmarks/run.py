"""Benchmark runner for the Guardian AI moderation platform.

Measures:
  1. Image false-positive rate on benign content (baseline vs. full pipeline)
  2. False-positive reduction percentage
  3. Text moderation accuracy (toxic/benign classification)
  4. Multi-modal context disambiguation (swimsuit + caption)
  5. Throughput (images per minute) on the current hardware

Produces a JSON + Markdown report in benchmarks/report/.
"""

import io
import json
import os
import time
from typing import Dict, List, Optional

from .baseline import SingleModelBaseline
from .data_generator import BENIGN_IMAGE_CATEGORIES, TEXT_SAMPLES, generate_all_benign
from .dataset import load_folder_dataset
from .metrics import accuracy, class_report, false_positive_rate


class BenchmarkRunner:
    def __init__(self, threshold: float = 0.4):
        from app.services.fusion_engine import FusionEngine
        from app.services.image_moderation import ImageModerationService
        from app.services.text_moderation import TextModerationService

        self.threshold = threshold
        self.image_service = ImageModerationService()
        self.text_service = TextModerationService()
        self.fusion = FusionEngine()
        # Naive NSFW detectors typically flag at a low threshold, producing
        # more false positives on benign content.
        self.baseline = SingleModelBaseline(self.image_service, threshold=0.3)
        self.results: Dict = {}

    # --- Individual benchmarks -------------------------------------------

    def benchmark_image_false_positives(self, dataset: Dict[str, List]) -> Dict:
        """FP rate on benign images: naive baseline vs. full Guardian pipeline.

        Also reports mean-risk reduction, which demonstrates the context-aware
        suppression mechanism even on synthetic data. FP-rate is only
        meaningful once real ambiguous images are provided via the folder
        dataset loader (real NSFW detectors cannot be triggered by synthetic
        flat-color images).
        """
        benign_images = []
        for cat in BENIGN_IMAGE_CATEGORIES:
            benign_images.extend(dataset.get(cat, []))
        benign_images.extend(dataset.get("benign", []))

        labels = [lbl == "toxic" for lbl, _ in benign_images]
        baseline_pred = []
        guardian_pred = []
        baseline_risks = []
        guardian_risks = []

        for lbl, buf in benign_images:
            buf.seek(0)
            baseline_risks.append(self.baseline.risk(buf))
            baseline_pred.append(self.baseline.is_flagged(buf))

            buf.seek(0)
            # Full pipeline: image + benign caption context
            image_result = self.image_service.moderate(buf)
            text_result = self.text_service.moderate("safe and neutral everyday content")
            final = self.fusion.fuse(image_result, text_result, "")
            guardian_risks.append(final["confidence"])
            guardian_pred.append(not final["safe"])

        baseline_fp = false_positive_rate(labels, baseline_pred)
        guardian_fp = false_positive_rate(labels, guardian_pred)
        reduction = 0.0
        if baseline_fp > 0:
            reduction = (baseline_fp - guardian_fp) / baseline_fp * 100.0

        # Mean-risk reduction: how much does context-awareness dampen the
        # NSFW signal on benign content?
        mean_baseline_risk = sum(baseline_risks) / len(baseline_risks) if baseline_risks else 0.0
        mean_guardian_risk = sum(guardian_risks) / len(guardian_risks) if guardian_risks else 0.0
        risk_reduction = 0.0
        if mean_baseline_risk > 0:
            risk_reduction = (mean_baseline_risk - mean_guardian_risk) / mean_baseline_risk * 100.0

        return {
            "samples": len(labels),
            "baseline_fp_rate": round(baseline_fp, 4),
            "guardian_fp_rate": round(guardian_fp, 4),
            "fp_reduction_pct": round(reduction, 2),
            "baseline_flag_count": sum(baseline_pred),
            "guardian_flag_count": sum(guardian_pred),
            "mean_baseline_risk": round(mean_baseline_risk, 4),
            "mean_guardian_risk": round(mean_guardian_risk, 4),
            "mean_risk_reduction_pct": round(risk_reduction, 2),
        }

    def benchmark_text_accuracy(self) -> Dict:
        labels = [label == "toxic" for _, label in TEXT_SAMPLES]
        predicted = []
        scores = []
        for text, _ in TEXT_SAMPLES:
            result = self.text_service.moderate(text)
            risk = max(result["toxic"], result["threat"], result["harassment"],
                       result["profanity"], result["adult_promo"])
            scores.append(risk)
            predicted.append(risk >= 0.3)

        report = class_report(labels, predicted)
        report["threshold"] = 0.3
        return report

    def benchmark_context_disambiguation(self, dataset: Dict[str, List]) -> Dict:
        """Same image + safe vs. risky caption must change the verdict."""
        swimsuits = dataset.get("swimsuit_scene", [])
        if not swimsuits:
            return {"skipped": True, "reason": "no swimsuit samples"}

        correct = 0
        total = 0
        safe_captions = ["Family vacation at Goa", "Summer holiday at the beach"]
        risky_captions = ["Subscribe for adult content", "Click here for x-rated content"]

        for lbl, buf in swimsuits:
            buf.seek(0)
            image_result = self.image_service.moderate(buf)

            for sc in safe_captions:
                safe_decision = self.fusion.fuse(
                    image_result, self.text_service.moderate(sc), "")
                if safe_decision["safe"]:
                    correct += 1
                total += 1

            for rc in risky_captions:
                risky_decision = self.fusion.fuse(
                    image_result, self.text_service.moderate(rc), "")
                if not risky_decision["safe"]:
                    correct += 1
                total += 1

        return {
            "skipped": False,
            "samples": total,
            "correct": correct,
            "accuracy": round(correct / total, 4) if total else 0.0,
        }

    def benchmark_throughput(self, dataset: Dict[str, List], num_images: int = 10) -> Dict:
        """Measure images-per-minute through the image service."""
        samples = []
        for cat in BENIGN_IMAGE_CATEGORIES:
            samples.extend(dataset.get(cat, []))
        samples = samples[:num_images]
        if not samples:
            return {"skipped": True}

        start = time.perf_counter()
        for _, buf in samples:
            buf.seek(0)
            self.image_service.moderate(buf)
        elapsed = time.perf_counter() - start

        per_image = elapsed / len(samples)
        images_per_minute = 60.0 / per_image if per_image > 0 else 0.0
        return {
            "skipped": False,
            "images_benchmarked": len(samples),
            "elapsed_seconds": round(elapsed, 3),
            "seconds_per_image": round(per_image, 3),
            "images_per_minute": round(images_per_minute, 1),
            "device": "cpu",
        }

    # --- Orchestration ---------------------------------------------------

    def run_all(self, folder_dataset: Optional[str] = None) -> Dict:
        synthetic = generate_all_benign(count_per_category=8)
        extra = load_folder_dataset(folder_dataset) if folder_dataset else {}

        # Merge real images in under their category keys when present
        for label, samples in extra.items():
            if label in synthetic:
                synthetic[label].extend(samples)
            else:
                synthetic[label] = samples

        self.results = {
            "threshold": self.threshold,
            "image_false_positives": self.benchmark_image_false_positives(synthetic),
            "text_accuracy": self.benchmark_text_accuracy(),
            "context_disambiguation": self.benchmark_context_disambiguation(synthetic),
            "throughput": self.benchmark_throughput(synthetic, num_images=10),
        }
        return self.results

    def save_report(self, out_dir: Optional[str] = None) -> str:
        if out_dir is None:
            out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "report"))
        os.makedirs(out_dir, exist_ok=True)
        json_path = os.path.join(out_dir, "benchmark_results.json")
        with open(json_path, "w") as f:
            json.dump(self.results, f, indent=2)

        md = self.render_markdown()
        md_path = os.path.join(out_dir, "benchmark_report.md")
        with open(md_path, "w") as f:
            f.write(md)
        return md_path

    def render_markdown(self) -> str:
        r = self.results
        fp = r["image_false_positives"]
        tx = r["text_accuracy"]
        ctx = r["context_disambiguation"]
        tp = r["throughput"]

        lines = [
            "# Guardian AI Benchmark Report",
            "",
            f"- **Decision threshold:** {r['threshold']}",
            f"- **Device:** {tp.get('device', 'n/a')}",
            "",
            "## 1. Image False-Positive Rate (Benign Content)",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Samples | {fp['samples']} |",
            f"| Naive baseline FP rate | {fp['baseline_fp_rate']:.1%} |",
            f"| Guardian AI FP rate | {fp['guardian_fp_rate']:.1%} |",
            f"| **False-positive reduction** | **{fp['fp_reduction_pct']:.1f}%** |",
            f"| Baseline flagged | {fp['baseline_flag_count']} |",
            f"| Guardian flagged | {fp['guardian_flag_count']} |",
            f"| Mean baseline risk | {fp['mean_baseline_risk']:.3f} |",
            f"| Mean Guardian risk | {fp['mean_guardian_risk']:.3f} |",
            f"| **Mean risk reduction** | **{fp['mean_risk_reduction_pct']:.1f}%** |",
            "",
            "> **Note on synthetic data:** FP-rate only becomes meaningful when "
            "real ambiguous images are supplied. CLIP trained on real photos "
            "will not flag flat-color synthetic images as explicit, so the "
            "naive baseline cannot be triggered by generated data. Use "
            "`python run_benchmark.py --dataset <folder>` with a `benign/` "
            "subfolder to measure false positives on real benign content. "
            "Toxic samples are not included in this false-positive metric.",
            "",
            "## 2. Text Moderation Accuracy",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Accuracy | {tx['accuracy']:.1%} |",
            f"| Precision | {tx['precision']:.1%} |",
            f"| Recall | {tx['recall']:.1%} |",
            f"| F1 | {tx['f1']:.1%} |",
            f"| FP rate | {tx['false_positive_rate']:.1%} |",
            f"| FN rate | {tx['false_negative_rate']:.1%} |",
            f"| Support | {tx['support']} |",
            "",
            "## 3. Multi-Modal Context Disambiguation",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Samples | {ctx.get('samples', 0)} |",
            f"| Accuracy | {ctx.get('accuracy', 0):.1%} |",
            "",
            "## 4. Throughput",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Images | {tp.get('images_benchmarked', 0)} |",
            f"| Seconds / image | {tp.get('seconds_per_image', 0):.2f} |",
            f"| **Images / minute** | **{tp.get('images_per_minute', 0):.0f}** |",
            "",
            "---",
            f"*Generated automatically by `benchmarks/run.py`*",
            "",
        ]
        return "\n".join(lines)


def run_cli(folder_dataset: Optional[str] = None):
    runner = BenchmarkRunner()
    print("Running Guardian AI benchmarks...")
    runner.run_all(folder_dataset=folder_dataset)
    path = runner.save_report()
    print(runner.render_markdown())
    print(f"\nReport saved to {os.path.abspath(path)}")
    return runner.results


if __name__ == "__main__":
    run_cli()
