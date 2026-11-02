import io
import os
import tempfile

import cv2
import numpy as np
import pytest
from PIL import Image

from app.services.video_moderation import VideoModerationService
from app.services.fusion_engine import FusionEngine


class FakeImageService:
    """Deterministic image service that flags frames beyond a threshold."""

    def __init__(self):
        self.calls = 0

    def moderate(self, image_bytes):
        self.calls += 1
        # Pretend every other frame is high-risk
        risk = 0.9 if self.calls % 2 == 1 else 0.1
        return {
            "nsfw_score": risk,
            "violence_score": 0.0,
            "weapon_score": 0.0,
            "hate_symbol_score": 0.0,
            "drugs_score": 0.0,
            "safe_score": 1.0 - risk,
            "medical_score": 0.0,
            "artistic_score": 0.0,
        }


def make_video_bytes(num_frames=30, fps=10):
    w, h = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
        tmp_path = tmp_file.name
    try:
        out = cv2.VideoWriter(tmp_path, fourcc, fps, (w, h))
        for i in range(num_frames):
            frame = np.full((h, w, 3), 30 + i, dtype=np.uint8)
            out.write(frame)
        out.release()
        with open(tmp_path, "rb") as f:
            return io.BytesIO(f.read())
    finally:
        os.unlink(tmp_path)


@pytest.fixture(scope="module")
def video_service():
    return VideoModerationService(
        image_service=FakeImageService(),
        fusion_engine=FusionEngine(),
        sample_interval_seconds=1.0,
        max_frames=120,
    )


def test_extract_frames_returns_expected_count(video_service):
    frames = video_service._extract_frames(make_video_bytes(30, 10))
    # 30 frames @10fps = 3s, sampled every 1s -> 3 frames (0.0, 1.0, 2.0)
    assert len(frames) == 3
    timestamps = [t for t, _ in frames]
    assert timestamps == [0.0, 1.0, 2.0]


def test_moderate_aggregates_flagged_frames(video_service):
    result = video_service.moderate(make_video_bytes(30, 10))
    assert result["frames_analyzed"] == 3
    assert result["scores"]["worst_risk"] > 0.4
    assert len(result["flagged_frames"]) > 0
    assert result["action"] in ("reject", "review")


def test_moderate_empty_video(video_service):
    result = video_service.moderate(io.BytesIO(b"not a video"))
    assert result["safe"] is True
    assert result["frames_analyzed"] == 0


def test_video_result_has_explanation(video_service):
    result = video_service.moderate(make_video_bytes(30, 10))
    assert "Analyzed 3 frames" in result["explanation"]


def test_image_is_pil_and_rgb():
    svc = VideoModerationService(
        image_service=FakeImageService(),
        fusion_engine=FusionEngine(),
        sample_interval_seconds=1.0,
        max_frames=120,
    )
    frames = svc._extract_frames(make_video_bytes(10, 10))
    assert len(frames) == 1
    img = frames[0][1]
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
