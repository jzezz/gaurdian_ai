import io
import os
import tempfile
import warnings
from typing import Dict, Any, List, Tuple

import cv2
import numpy as np
from PIL import Image

warnings.filterwarnings("ignore")


class VideoModerationService:
    """
    Extracts frames from a video at a configurable interval and runs the
    image moderation pipeline on each frame. Aggregates per-frame scores
    into a single video-level decision with timestamps of flagged frames.
    """

    def __init__(self, image_service, fusion_engine, sample_interval_seconds: float = 2.0,
                 max_frames: int = 120):
        self.image_service = image_service
        self.fusion_engine = fusion_engine
        self.sample_interval_seconds = sample_interval_seconds
        self.max_frames = max_frames

    def _extract_frames(self, video_bytes: io.BytesIO) -> List[Tuple[float, Image.Image]]:
        """
        Decode the video and yield (timestamp_seconds, PIL.Image) tuples at
        the configured sampling interval. Returns an empty list on failure.
        """
        frames: List[Tuple[float, Image.Image]] = []
        tmp_path = None
        try:
            video_bytes.seek(0)
            fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
            with os.fdopen(fd, "wb") as tmp_file:
                tmp_file.write(video_bytes.getvalue())

            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                return frames

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_interval = max(1, int(round(fps * self.sample_interval_seconds)))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

            idx = 0
            sampled = 0
            while sampled < self.max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                if idx % frame_interval == 0:
                    timestamp = idx / fps if fps > 0 else idx
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append((round(timestamp, 2), Image.fromarray(rgb)))
                    sampled += 1
                idx += 1
                if frame_count and idx >= frame_count:
                    break
            cap.release()
        except Exception as e:
            print(f"Video frame extraction error: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
        return frames

    def _aggregate(self, per_frame_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine per-frame risk scores into video-level aggregates:
        worst-case (max), mean, and count of flagged frames.
        """
        if not per_frame_results:
            return {
                "worst_risk": 0.0,
                "mean_risk": 0.0,
                "flagged_frames": [],
            }

        max_risk = max(r["risk"] for r in per_frame_results)
        mean_risk = sum(r["risk"] for r in per_frame_results) / len(per_frame_results)
        flagged = [r for r in per_frame_results if r["risk"] >= 0.4]

        return {
            "worst_risk": round(max_risk, 4),
            "mean_risk": round(mean_risk, 4),
            "flagged_frames": flagged,
        }

    def moderate(self, video_bytes: io.BytesIO) -> Dict[str, Any]:
        """
        Run full video moderation:
        1. Extract sampled frames
        2. Run image moderation on each frame
        3. Fuse with any caption/OCR signals per frame
        4. Aggregate into a final video-level decision
        """
        frames = self._extract_frames(video_bytes)
        if not frames:
            return {
                "safe": True,
                "confidence": 0.0,
                "action": "approve",
                "frames_analyzed": 0,
                "duration_seconds": 0.0,
                "scores": {
                    "worst_risk": 0.0,
                    "mean_risk": 0.0,
                },
                "flagged_frames": [],
                "explanation": "Video could not be decoded or contains no frames. No content found.",
                "flagged_categories": [],
            }

        per_frame_results = []
        duration = frames[-1][0]

        for timestamp, image in frames:
            buf = io.BytesIO()
            image.save(buf, format="JPEG")
            buf.seek(0)

            image_result = self.image_service.moderate(buf)
            frame_fused = self.fusion_engine.fuse(image_result, None, "")
            per_frame_results.append({
                "timestamp": timestamp,
                "risk": frame_fused["confidence"],
                "scores": image_result,
                "flagged_categories": frame_fused["flagged_categories"],
            })

        aggregate = self._aggregate(per_frame_results)
        worst_risk = aggregate["worst_risk"]
        mean_risk = aggregate["mean_risk"]

        if worst_risk >= self.fusion_engine.reject_threshold:
            action, safe = "reject", False
        elif worst_risk >= self.fusion_engine.review_threshold:
            action, safe = "review", False
        else:
            action, safe = "approve", True

        flagged_cats = set()
        for f in aggregate["flagged_frames"]:
            flagged_cats.update(f["flagged_categories"])

        explanation = self._build_explanation(
            worst_risk, mean_risk, len(frames), aggregate["flagged_frames"], action
        )

        return {
            "safe": safe,
            "confidence": round(worst_risk, 4),
            "action": action,
            "frames_analyzed": len(frames),
            "duration_seconds": duration,
            "scores": {
                "worst_risk": worst_risk,
                "mean_risk": mean_risk,
            },
            "flagged_frames": [
                {"timestamp": f["timestamp"], "categories": f["flagged_categories"]}
                for f in aggregate["flagged_frames"]
            ],
            "explanation": explanation,
            "flagged_categories": sorted(flagged_cats),
        }

    def _build_explanation(self, worst_risk: float, mean_risk: float,
                           num_frames: int, flagged_frames: List[Dict],
                           action: str) -> str:
        parts = [
            f"Analyzed {num_frames} frames sampled from the video.",
            f"Highest-risk frame score: {worst_risk:.0%}. Average frame score: {mean_risk:.0%}."
        ]
        if flagged_frames:
            timestamps = ", ".join(f"{f['timestamp']}s" for f in flagged_frames[:10])
            parts.append(f"Flagged frame timestamps: {timestamps}.")
        else:
            parts.append("No frames exceeded the risk threshold.")

        if action == "reject":
            parts.append("Overall recommendation: Reject Video.")
        elif action == "review":
            parts.append("Overall recommendation: Needs Human Review.")
        else:
            parts.append("Overall recommendation: Approve.")

        return "\n\n".join(parts)
