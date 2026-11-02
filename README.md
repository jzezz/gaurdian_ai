# Guardian AI

Guardian AI is a local, multimodal content moderation demo. It combines image classification, text classification, OCR, rule-based score fusion, and sampled video frames to return an explainable recommendation. It is a prototype for developer evaluation and human review, not a production moderation service.

![Guardian AI moderation interface](docs/screenshots/guardian-ai.jpg)

<details>
<summary>Text and video screens</summary>

![Text moderation screen](docs/screenshots/guardian-ai-text.jpg)

![Video moderation screen](docs/screenshots/guardian-ai-video.jpg)
</details>

## What it does

- **Images:** CLIP zero-shot image categories, OCR text extraction, optional caption analysis, and a fused approve/review/reject recommendation.
- **Text:** BART zero-shot scoring for toxicity, threats, harassment, profanity, and adult promotion.
- **Video:** asynchronous frame sampling and aggregation, with timestamps for frames that cross the review threshold.
- **API:** FastAPI endpoints with interactive OpenAPI docs.
- **Web app:** React, TypeScript, and Vite interface for submitting image, text, and video content.

The models are downloaded by Transformers/EasyOCR when first initialized. CPU inference is the default and model loading can require several gigabytes of RAM and disk space. The image and text services fall back to permissive placeholder responses if their models fail to load; do not treat those responses as trustworthy moderation decisions.

## Run locally

### Requirements

- Python 3.11 recommended
- Node.js 20+
- Git
- For video support, an OpenCV-compatible video codec

### Start the API

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd backend
python run.py
```

The API listens on `http://localhost:8000`. The OpenAPI UI is at `http://localhost:8000/docs`; health check: `http://localhost:8000/health`.

### Start the web app

In a second terminal from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. To use a different API origin, set `VITE_API_URL` before building or starting Vite, for example `VITE_API_URL=http://localhost:8000`.

### Docker Compose

```bash
docker compose up --build
```

Open `http://localhost:3000`. Compose builds the browser-facing app with `http://localhost:8000` as its API URL. Set `VITE_API_URL` in the shell or an untracked `.env` file if the browser should reach the API at another origin. The backend image downloads the configured models on startup.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Health probe |
| `GET` | `/` | Service and version info |
| `POST` | `/moderate/image` | Multipart image upload; optional `caption` |
| `POST` | `/moderate/text` | JSON body: `{"text":"..."}` |
| `POST` | `/moderate/video` | Multipart video upload; optional `sample_interval` in seconds |
| `GET` | `/moderate/status/{job_id}` | Poll an asynchronous video job |
| `GET` | `/logs?limit=50` | Read recent in-memory requests |

Example text request:

```bash
curl -X POST http://localhost:8000/moderate/text \
  -H "Content-Type: application/json" \
  -d '{"text":"Thanks for your help today."}'
```

Image and video endpoints accept multipart form data with a `file` field. Video submission returns a `job_id`; poll `/moderate/status/{job_id}` until its status is `completed` or `failed`.

## Analytics and evaluation

The project includes a benchmark runner that reports benign-image false-positive rates, text classification precision/recall/F1, caption context checks, and image throughput. Run it from the repository root:

```bash
python backend/run_benchmark.py
# Optional labeled images: dataset/benign/ (used for false-positive analysis)
python backend/run_benchmark.py --dataset dataset
```

The runner writes JSON and Markdown reports under `backend/report/` (ignored by Git). The bundled text set is small and hand-curated, and the generated image set is synthetic. Results from these fixtures are smoke-test analytics, not an independent accuracy study. The optional image set is used only for benign false-positive analysis; toxic-folder samples are not included in that metric. Use a representative, consented, labeled dataset and record hardware/model versions before making quality or throughput claims. No model benchmark has been run for this repository snapshot.

### Repository checks

| Check | Latest local result |
|---|---|
| Backend tests | 18 passed with `python -m pytest -q` |
| Frontend production build | Passed with `npm run build` |
| Model quality / throughput | Not run; requires model downloads and a benchmark run |

GitHub Actions runs the backend tests and frontend production build on pushes and pull requests.

## Development checks

```bash
python -m pip install -r backend/requirements-dev.txt numpy pillow opencv-python-headless
python -m pytest -q
cd frontend && npm ci && npm run build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## Known limitations before production

- Model-load failures currently fall back to permissive “safe” scores; fail closed or clearly mark model availability before using this for decisions.
- Logs and asynchronous video jobs live only in memory and disappear on restart.
- The API has no authentication, rate limiting, upload-size limits, or durable job queue.
- Video samples do not currently run OCR; supplied captions are fused with the frame risk.
- The moderation thresholds and category prompts need validation and calibration against representative data.

## License

MIT. See [LICENSE](LICENSE).
