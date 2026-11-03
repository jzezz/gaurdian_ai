# Guardian AI

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green)

**Multimodal content moderation that explains its decisions.** Guardian AI analyzes images, text, and video with CLIP, BART, and OCR, then fuses the signals into an explainable **approve / review / reject** recommendation.

> A prototype for developer evaluation and human review, not a production moderation service.

## Live demo

**Frontend:** [frontend-seven-olive-yg3zjqy2wn.vercel.app](https://frontend-seven-olive-yg3zjqy2wn.vercel.app)

The web app needs a running backend API. If the hosted demo can't reach one, run the backend locally (see [Quick start](#quick-start)) and open the app on `localhost`.

![Guardian AI moderation interface](docs/screenshots/guardian-ai.jpg)

<details>
<summary>More screenshots: text and video moderation</summary>

![Text moderation](docs/screenshots/guardian-ai-text.jpg)
![Video moderation](docs/screenshots/guardian-ai-video.jpg)
</details>

## Features

| Content | How it is analyzed |
|---|---|
| **Images** | CLIP zero-shot categories, OCR text extraction, optional caption analysis |
| **Text** | BART zero-shot scoring for toxicity, threats, harassment, profanity, adult promotion |
| **Video** | Asynchronous frame sampling and aggregation; timestamps for frames above the review threshold |

- **Score fusion:** rule-based engine combines image, OCR, and caption signals into one recommendation with per-category confidence scores.
- **REST API:** FastAPI with interactive OpenAPI docs.
- **Web app:** React + TypeScript + Vite interface for image, text, and video submission.
- **Tested:** 18 backend tests, a frontend production build, and a GitHub Actions workflow.

## How it works

```
Image / Text / Video
        │
        ├─ Image ──► CLIP categories ─┐
        │            EasyOCR text ────┤
        ├─ Text ───► BART scoring ────┼──► Fusion engine ──► approve / review / reject
        └─ Video ──► frame sampling ──┘     (explainable scores)
```

## Tech stack

| Area | Tools |
|---|---|
| Models | PyTorch, Hugging Face Transformers (CLIP, BART), EasyOCR, OpenCV |
| Backend | Python, FastAPI, Uvicorn |
| Frontend | React, TypeScript, Vite |
| DevOps | Docker Compose, GitHub Actions, pytest |

## Quick start

**Requirements:** Python 3.11, Node.js 20+, Git. Models download on first run and may need several GB of disk and RAM. Inference runs on CPU by default.

### 1. Backend

```powershell
git clone https://github.com/jzezz/gaurdian_ai.git
cd gaurdian_ai
python -m venv .venv
.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd backend
python run.py
```

API: `http://localhost:8000`, docs: `http://localhost:8000/docs`, health: `http://localhost:8000/health`.

### 2. Frontend

In a second terminal from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. To point at a different API, set `VITE_API_URL` (e.g. `VITE_API_URL=http://localhost:8000`) before starting.

### Docker (optional)

```bash
docker compose up --build
```
Compose builds the app with `http://localhost:8000` as its API URL. This setup has not been verified yet.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/moderate/image` | Upload an image (`file`), optional `caption` |
| `POST` | `/moderate/text` | JSON body: `{"text": "..."}` |
| `POST` | `/moderate/video` | Upload a video (`file`), optional `sample_interval` in seconds. Returns a `job_id` |
| `GET` | `/moderate/status/{job_id}` | Poll a video job until `completed` or `failed` |
| `GET` | `/health` | Health probe |
| `GET` | `/logs?limit=50` | Recent in-memory requests (debug only) |

```bash
curl -X POST http://localhost:8000/moderate/text \
  -H "Content-Type: application/json" \
  -d '{"text":"Thanks for your help today."}'
```

## Evaluation

A built-in benchmark runner reports text precision/recall/F1, benign-image false positives, caption-context checks, and image throughput:

```bash
python backend/run_benchmark.py
python backend/run_benchmark.py --dataset dataset   # optional labeled benign images
```

Reports are written to `backend/report/` (Git-ignored).

| Metric | Result | Notes |
|---|---:|---|
| Text classification | **95.0% accuracy**, 90.9% precision, 100% recall, **95.2% F1** | 20 hand-curated samples (1 false positive, 0 false negatives) |
| Context checks | **100% (32/32)** | Generated fixtures |
| Benign image false positives | **0 / 56** | Synthetic images; neither baseline nor Guardian flagged any |
| Image throughput | **~690 images/min** (0.087 s/image) | 10 images, CPU |

![Benchmark results](docs/analytics/benchmark-results.png)
<!-- Add a chart or screenshot of the benchmark report here -->

**Read these as smoke tests, not accuracy claims.** The text set is small, the image and context sets are synthetic, and the run did not measure concurrency or end-to-end API latency. A real evaluation needs a representative, consented, labeled dataset with documented hardware and model versions.

## Limitations

This is a prototype. Before exposing it to untrusted users:

- **Model failures can look safe.** If a model fails to load, services fall back to permissive scores. Add a fail-closed mode and a model-readiness check.
- **No access control.** The API has no authentication, rate limiting, or upload-size limits, and `/logs` exposes recent request content.
- **CORS is open to all origins.** Restrict it to your frontend's domain.
- **State is in-memory.** Video jobs and logs are lost on restart and have no retention limits.
- **Video OCR is not supported.** Frame risk is fused with any supplied caption only.
- **Thresholds are uncalibrated.** Category prompts and decision thresholds need validation on representative data.

## Development

```bash
python -m pip install -r backend/requirements-dev.txt numpy pillow opencv-python-headless
python -m pytest -q
cd frontend && npm ci && npm run build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Author

**Jabez Bodkhe**: [LinkedIn](https://www.linkedin.com/in/jabez-bodkhe/) | [GitHub](https://github.com/jzezz) | [Portfolio](https://jzezz-portfolio.vercel.app)

## License

MIT. See [LICENSE](LICENSE).
