import threading
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    def __init__(self, job_type: str, params: Dict[str, Any]):
        self.job_id = str(uuid.uuid4())
        self.job_type = job_type
        self.params = params
        self.status = JobStatus.PENDING
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None


class JobManager:
    """
    Lightweight in-memory async job queue with a background worker thread.
    For production this should be replaced by a durable queue (e.g. Redis +
    Celery/RQ), but it satisfies the Phase 4 async video workflow.
    """

    def __init__(self, num_workers: int = 1):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._queue: list = []
        self._condition = threading.Condition(self._lock)
        self._workers = []
        self._stop = False
        self._num_workers = num_workers

    def start(self):
        for _ in range(self._num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)

    def stop(self):
        with self._condition:
            self._stop = True
            self._condition.notify_all()

    def submit(self, job_type: str, params: Dict[str, Any]) -> str:
        job = Job(job_type, params)
        with self._condition:
            self._jobs[job.job_id] = job
            self._queue.append(job.job_id)
            self._condition.notify()
        return job.job_id

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def _worker_loop(self):
        while True:
            with self._condition:
                while not self._stop and not self._queue:
                    self._condition.wait()
                if self._stop and not self._queue:
                    return
                job_id = self._queue.pop(0)
                job = self._jobs.get(job_id)

            if job is None:
                continue

            job.status = JobStatus.PROCESSING
            job.started_at = time.time()
            try:
                handler: Callable = self._handlers[job.job_type]
                job.result = handler(job.params)
                job.status = JobStatus.COMPLETED
            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
            finally:
                job.completed_at = time.time()

    _handlers: Dict[str, Callable] = {}

    def register_handler(self, job_type: str, handler: Callable):
        self._handlers[job_type] = handler

    def to_dict(self, job: Job) -> Dict[str, Any]:
        return {
            "job_id": job.job_id,
            "type": job.job_type,
            "status": job.status.value,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "result": job.result,
            "error": job.error,
        }
