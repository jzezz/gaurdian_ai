from typing import Optional, Dict, Any, List

class FusionEngine:
    """
    Combines vision, text, and OCR signals into a single explainable decision.
    Uses a weighted rule-based approach for v1.0.
    """

    def __init__(self):
        # Configurable weights
        self.vision_weight = 0.5
        self.text_weight = 0.35
        self.ocr_weight = 0.15
        # Thresholds
        self.reject_threshold = 0.7
        self.review_threshold = 0.4
        # A single dominant signal at this level rejects outright
        self.strong_signal_threshold = 0.8

    def fuse(self, image_result: Dict[str, Any], text_result: Optional[Dict[str, Any]], ocr_text: str) -> Dict[str, Any]:
        # Vision risk score (max of all risk categories)
        vision_risk = max(
            image_result.get("nsfw_score", 0.0),
            image_result.get("violence_score", 0.0),
            image_result.get("weapon_score", 0.0),
            image_result.get("hate_symbol_score", 0.0),
            image_result.get("drugs_score", 0.0),
        )

        # Text risk score
        text_risk = 0.0
        if text_result:
            text_risk = max(
                text_result.get("toxic", 0.0),
                text_result.get("threat", 0.0),
                text_result.get("harassment", 0.0),
                text_result.get("profanity", 0.0),
                text_result.get("adult_promo", 0.0),
            )

        # OCR contribution (if text was found in image, boost text signal)
        ocr_boost = 0.0
        if ocr_text and text_result:
            ocr_boost = 0.1  # Slight boost when OCR text is present and flagged

        # Weighted fusion
        overall_risk = (
            self.vision_weight * vision_risk +
            self.text_weight * text_risk +
            ocr_boost
        )
        overall_risk = min(1.0, overall_risk)

        # A single dominant signal (e.g. 95% explicit) rejects outright even if
        # the weighted score is dampened by other signals.
        max_single_risk = max(vision_risk, text_risk)

        # Determine action
        if overall_risk >= self.reject_threshold or max_single_risk >= self.strong_signal_threshold:
            action = "reject"
            safe = False
        elif overall_risk >= self.review_threshold:
            action = "review"
            safe = False
        else:
            action = "approve"
            safe = True

        # Build explanation
        explanation = self._generate_explanation(
            image_result, text_result, ocr_text, vision_risk, text_risk, overall_risk, action
        )

        # Flagged categories
        flagged = []
        if image_result.get("nsfw_score", 0) > 0.4:
            flagged.append("explicit content")
        if image_result.get("violence_score", 0) > 0.4:
            flagged.append("violence")
        if image_result.get("weapon_score", 0) > 0.4:
            flagged.append("weapons")
        if image_result.get("hate_symbol_score", 0) > 0.4:
            flagged.append("hate symbols")
        if image_result.get("drugs_score", 0) > 0.4:
            flagged.append("drugs")
        if text_result:
            if text_result.get("toxic", 0) > 0.4:
                flagged.append("toxicity")
            if text_result.get("threat", 0) > 0.4:
                flagged.append("threats")
            if text_result.get("harassment", 0) > 0.4:
                flagged.append("harassment")
            if text_result.get("profanity", 0) > 0.4:
                flagged.append("profanity")
            if text_result.get("adult_promo", 0) > 0.4:
                flagged.append("adult promotion")

        return {
            "safe": safe,
            "confidence": round(overall_risk, 4),
            "action": action,
            "scores": {
                "vision": image_result,
                "text": text_result or {},
                "overall_risk": round(overall_risk, 4),
            },
            "explanation": explanation,
            "flagged_categories": flagged,
        }

    def _generate_explanation(
        self, image_result: Dict, text_result: Optional[Dict],
        ocr_text: str, vision_risk: float, text_risk: float,
        overall_risk: float, action: str
    ) -> str:
        parts = []

        # Vision explanation
        if vision_risk > 0.3:
            if image_result.get("nsfw_score", 0) > 0.4:
                parts.append(f"Visual analysis detected explicit content with {image_result['nsfw_score']:.0%} confidence.")
            if image_result.get("violence_score", 0) > 0.4:
                parts.append(f"Visual analysis detected violent imagery with {image_result['violence_score']:.0%} confidence.")
            if image_result.get("weapon_score", 0) > 0.4:
                parts.append(f"Visual analysis detected weapons with {image_result['weapon_score']:.0%} confidence.")
            if image_result.get("hate_symbol_score", 0) > 0.4:
                parts.append(f"Visual analysis detected hate symbols with {image_result['hate_symbol_score']:.0%} confidence.")
            if image_result.get("drugs_score", 0) > 0.4:
                parts.append(f"Visual analysis detected drug-related content with {image_result['drugs_score']:.0%} confidence.")
            if image_result.get("medical_score", 0) > 0.3:
                parts.append("Context suggests medical or educational content, which may reduce risk.")
            if image_result.get("artistic_score", 0) > 0.3:
                parts.append("Context suggests artistic or cultural content, which may reduce risk.")
        else:
            parts.append("Visual analysis found no concerning content.")

        # Text explanation
        if text_result and text_risk > 0.3:
            if text_result.get("adult_promo", 0) > 0.4:
                parts.append(f"Caption or text contains promotional language associated with adult content ({text_result['adult_promo']:.0%} confidence).")
            if text_result.get("toxic", 0) > 0.4:
                parts.append(f"Text analysis detected toxic or hateful language ({text_result['toxic']:.0%} confidence).")
            if text_result.get("threat", 0) > 0.4:
                parts.append(f"Text analysis detected threatening language ({text_result['threat']:.0%} confidence).")
            if text_result.get("harassment", 0) > 0.4:
                parts.append(f"Text analysis detected harassment ({text_result['harassment']:.0%} confidence).")
            if text_result.get("profanity", 0) > 0.4:
                parts.append(f"Text analysis detected profanity ({text_result['profanity']:.0%} confidence).")
        elif text_result:
            parts.append("Text analysis found no concerning language.")

        # OCR explanation
        if ocr_text:
            parts.append(f"OCR extracted text from the image: \"{ocr_text[:100]}{'...' if len(ocr_text) > 100 else ''}\"")

        # Final recommendation
        if action == "reject":
            parts.append(f"Overall recommendation: Reject Upload. Risk score: {overall_risk:.0%}")
        elif action == "review":
            parts.append(f"Overall recommendation: Needs Human Review. Risk score: {overall_risk:.0%}")
        else:
            parts.append(f"Overall recommendation: Approve. Risk score: {overall_risk:.0%}")

        return "\n\n".join(parts)
