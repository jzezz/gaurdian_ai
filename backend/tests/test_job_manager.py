import time

import pytest

from app.services.job_manager import JobManager, JobStatus


@pytest.fixture
def manager():
    m = JobManager(num_workers=1)
    m.start()
    yield m
    m.stop()


def test_job_completes(manager):
    manager.register_handler("square", lambda p: p["x"] * p["x"])
    job_id = manager.submit("square", {"x": 6})

    for _ in range(100):
        time.sleep(0.02)
        job = manager.get(job_id)
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            break

    assert job.status == JobStatus.COMPLETED
    assert job.result == 36


def test_job_failure_captured(manager):
    def bad(params):
        raise ValueError("boom")

    manager.register_handler("bad", bad)
    job_id = manager.submit("bad", {})
    for _ in range(100):
        time.sleep(0.02)
        job = manager.get(job_id)
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            break

    assert job.status == JobStatus.FAILED
    assert "boom" in job.error


def test_get_returns_none_for_missing(manager):
    assert manager.get("does-not-exist") is None


def test_submit_returns_unique_ids(manager):
    a = manager.submit("noop", {})
    b = manager.submit("noop", {})
    assert a != b
