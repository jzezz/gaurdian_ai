# Project status

Guardian AI is a functional prototype intended for local development and evaluation. It is not production-ready.

## Verified in this workspace

- React/TypeScript frontend production build succeeds.
- Backend tests pass from the repository root with `python -m pytest -q` (18 passed).
- GitHub Actions is configured to run the backend tests and frontend build.
- Docker Compose and README setup instructions are present.

Re-run the commands above after changes; this file is a status summary, not a substitute for current CI results.

## Current limitations

- Image and text services return permissive fallback scores if their ML models fail to load.
- No authentication, rate limiting, upload-size limits, durable storage, or persistent job queue.
- Benchmark fixtures are synthetic or small hand-curated samples; model quality and throughput are not independently validated.
- Docker runtime and full model downloads have not been verified in this workspace.

See [README.md](README.md) for setup, API usage, evaluation notes, and release caveats.
