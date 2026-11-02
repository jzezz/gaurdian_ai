import io

import pytest
from PIL import Image

from app.services.fusion_engine import FusionEngine


def make_image_result(nsfw=0.0, violence=0.0, weapon=0.0, hate=0.0, drugs=0.0):
    return {
        "nsfw_score": nsfw,
        "violence_score": violence,
        "weapon_score": weapon,
        "hate_symbol_score": hate,
        "drugs_score": drugs,
        "safe_score": 1.0 - max(nsfw, violence, weapon, hate, drugs),
        "medical_score": 0.0,
        "artistic_score": 0.0,
    }


def make_text_result(toxic=0.0, threat=0.0, harassment=0.0, profanity=0.0, adult_promo=0.0):
    return {
        "toxic": toxic,
        "threat": threat,
        "harassment": harassment,
        "profanity": profanity,
        "adult_promo": adult_promo,
        "safe_score": 1.0 - max(toxic, threat, harassment, profanity, adult_promo),
        "safe": max(toxic, threat, harassment, profanity, adult_promo) < 0.3,
        "confidence": max(toxic, threat, harassment, profanity, adult_promo),
    }


@pytest.fixture
def fusion():
    return FusionEngine()


def test_fusion_approves_clean_content(fusion):
    result = fusion.fuse(make_image_result(), make_text_result(), "")
    assert result["safe"] is True
    assert result["action"] == "approve"
    assert result["flagged_categories"] == []


def test_fusion_rejects_explicit_image(fusion):
    result = fusion.fuse(make_image_result(nsfw=0.95), make_text_result(), "")
    assert result["safe"] is False
    assert result["action"] == "reject"
    assert "explicit content" in result["flagged_categories"]


def test_fusion_rejects_violent_text(fusion):
    result = fusion.fuse(make_image_result(), make_text_result(threat=0.95), "")
    assert result["safe"] is False
    assert result["action"] == "reject"
    assert "threats" in result["flagged_categories"]


def test_swimsuit_context_disambiguation(fusion):
    # Same image, different captions - caption changes the verdict
    benign_image = make_image_result(nsfw=0.5)  # borderline image
    safe_caption = make_text_result()
    risky_caption = make_text_result(adult_promo=0.9)

    safe_decision = fusion.fuse(benign_image, safe_caption, "")
    risky_decision = fusion.fuse(benign_image, risky_caption, "")

    assert risky_decision["confidence"] > safe_decision["confidence"]
    assert "adult promotion" in risky_decision["flagged_categories"]


def test_ocr_boost_increases_risk(fusion):
    base = fusion.fuse(make_image_result(nsfw=0.3), make_text_result(toxic=0.5), "")
    boosted = fusion.fuse(make_image_result(nsfw=0.3), make_text_result(toxic=0.5), "kill them all")
    assert boosted["confidence"] >= base["confidence"]


def test_explanation_contains_recommendation(fusion):
    result = fusion.fuse(make_image_result(nsfw=0.9), make_text_result(), "")
    assert "Reject" in result["explanation"]


def test_review_threshold(fusion):
    # 0.5*vision + 0.35*text = 0.5*0.5 + 0.35*0.5 = 0.425 -> review (both signals < 0.8 strong)
    result = fusion.fuse(make_image_result(nsfw=0.5), make_text_result(toxic=0.5), "")
    assert result["action"] == "review"
    assert result["safe"] is False


def test_empty_text_result_handled(fusion):
    result = fusion.fuse(make_image_result(), None, "")
    assert result["safe"] is True
