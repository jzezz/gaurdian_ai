from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import io

from app.services.image_moderation import ImageModerationService
from app.services.text_moderation import TextModerationService
from app.services.ocr_service import OCRService
from app.services.fusion_engine import FusionEngine
from app.services.video_moderation import VideoModerationService
from app.services.job_manager import JobManager, JobStatus

app = FastAPI(
    title="Guardian AI",
    description="Context-Aware Multi-Modal Content Moderation Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
image_service = ImageModerationService()
text_service = TextModerationService()
ocr_service = OCRService()
fusion_engine = FusionEngine()
video_service = VideoModerationService(
    image_service=image_service,
    fusion_engine=fusion_engine,
    sample_interval_seconds=2.0,
    max_frames=120,
)

# Async job queue for video moderation
job_manager = JobManager(num_workers=1)


def _run_video_job(params):
    interval = params.get("sample_interval") or 2.0
    video_service.sample_interval_seconds = interval
    result = video_service.moderate(params["video_bytes"])
    caption = params.get("caption")
    if caption and result.get("frames_analyzed", 0):
        video_scores = result["scores"]
        decision = fusion_engine.fuse(
            {"nsfw_score": result["confidence"]}, text_service.moderate(caption), ""
        )
        result.update(decision)
        result["scores"]["video"] = video_scores
    return result


job_manager.register_handler("video", _run_video_job)
job_manager.start()

# In-memory store for logs (use DB in production)
moderation_logs: List[dict] = []

class TextModerationRequest(BaseModel):
    text: str

class ModerationResponse(BaseModel):
    safe: bool
    confidence: float
    action: str
    scores: dict
    explanation: str
    flagged_categories: List[str]

class TextModerationResponse(BaseModel):
    toxic: float
    threat: float
    harassment: float
    profanity: float
    adult_promo: float
    safe: bool
    confidence: float
    scores: dict
    explanation: str

class VideoModerationResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    error: Optional[str] = None
    result: Optional[dict] = None

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Guardian AI", "version": "1.0.0"}

@app.post("/moderate/image", response_model=ModerationResponse)
async def moderate_image(
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None)
):
    """
    Moderate an uploaded image. Optionally provide a caption for multi-modal analysis.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    image_bytes = io.BytesIO(contents)

    # Run image moderation
    image_result = image_service.moderate(image_bytes)

    # Run OCR on image
    ocr_text = ocr_service.extract_text(image_bytes)

    # Run text moderation on caption + OCR text
    text_result = None
    if caption or ocr_text:
        combined_text = " ".join(filter(None, [caption, ocr_text]))
        text_result = text_service.moderate(combined_text)

    # Fuse results
    final = fusion_engine.fuse(image_result, text_result, ocr_text)

    # Log result
    log_entry = {
        "type": "image",
        "filename": file.filename,
        "caption": caption,
        "result": final,
    }
    moderation_logs.append(log_entry)

    return ModerationResponse(**final)

@app.post("/moderate/text", response_model=TextModerationResponse)
async def moderate_text(request: TextModerationRequest):
    """
    Moderate plain text for toxicity, threats, harassment, and profanity.
    """
    result = text_service.moderate(request.text)

    explanation = build_text_explanation(result)

    log_entry = {
        "type": "text",
        "text": request.text[:200],
        "result": result,
    }
    moderation_logs.append(log_entry)

    scores = {
        "toxic": result["toxic"],
        "threat": result["threat"],
        "harassment": result["harassment"],
        "profanity": result["profanity"],
        "adult_promo": result["adult_promo"],
        "safe": result["safe_score"],
    }
    return TextModerationResponse(**result, scores=scores, explanation=explanation)


def build_text_explanation(result: dict) -> str:
    parts = []
    if result["toxic"] > 0.4:
        parts.append(f"Text analysis detected toxic or hateful language ({result['toxic']:.0%} confidence).")
    if result["threat"] > 0.4:
        parts.append(f"Text analysis detected threatening language ({result['threat']:.0%} confidence).")
    if result["harassment"] > 0.4:
        parts.append(f"Text analysis detected harassment ({result['harassment']:.0%} confidence).")
    if result["profanity"] > 0.4:
        parts.append(f"Text analysis detected profanity ({result['profanity']:.0%} confidence).")
    if result["adult_promo"] > 0.4:
        parts.append(f"Text contains promotional language associated with adult content ({result['adult_promo']:.0%} confidence).")
    if not parts:
        parts.append("Text analysis found no concerning language.")
    parts.append(f"Overall recommendation: {'Reject' if not result['safe'] else 'Approve'}. Confidence: {result['confidence']:.0%}")
    return "\n\n".join(parts)

@app.post("/moderate/video", response_model=VideoModerationResponse)
async def moderate_video(
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    sample_interval: float = Form(2.0),
):
    """
    Submit a video for frame-based moderation. Runs asynchronously;
    poll /moderate/status/{job_id} for the result.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File is empty")

    video_bytes = io.BytesIO(contents)
    params = {"video_bytes": video_bytes, "caption": caption, "sample_interval": sample_interval}
    job_id = job_manager.submit("video", params)

    log_entry = {
        "type": "video",
        "filename": file.filename,
        "job_id": job_id,
    }
    moderation_logs.append(log_entry)

    return VideoModerationResponse(job_id=job_id, status=JobStatus.PENDING.value)


@app.get("/moderate/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Poll the status and result of an async moderation job."""
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(job_id=job.job_id, status=job.status.value, error=job.error, result=job.result)


@app.get("/logs")
def get_logs(limit: int = 50):
    """Get recent moderation logs."""
    return {"logs": moderation_logs[-limit:][::-1]}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
