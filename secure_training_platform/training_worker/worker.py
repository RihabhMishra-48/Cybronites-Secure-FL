"""
Training Worker — Consumes jobs from queue and runs secure training.

Supports two modes:
1. Redis queue (production) — polls Redis for new jobs
2. In-process queue (development) — uses threading.Queue fallback
"""
from __future__ import annotations

import json
import uuid
import logging
import threading
import time
from datetime import datetime
from queue import Queue, Empty

from secure_training_platform.config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_QUEUE_NAME, MAX_CONCURRENT_JOBS
)
from secure_training_platform.database.db import execute_query, execute_insert
from secure_training_platform.dataset_vault.vault import DatasetVault
from secure_training_platform.key_manager.manager import KeyManager
from secure_training_platform.model_registry.registry import ModelRegistry
from secure_training_platform.training_worker.sandbox import TrainingSandbox

logger = logging.getLogger(__name__)

# In-process fallback queue
_fallback_queue: Queue = Queue()
_redis_available = False
_redis_client = None


def _init_redis():
    """Try to connect to Redis; fall back to in-process queue."""
    global _redis_available, _redis_client
    try:
        import redis
        _redis_client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
            decode_responses=False, socket_timeout=5
        )
        _redis_client.ping()
        _redis_available = True
        logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        _redis_available = False
        logger.warning(f"Redis unavailable ({e}), using in-process queue")


def submit_job(dataset_id: str, model_type: str, hyperparams: dict) -> str:
    """
    Submit a training job to the queue.
    
    Returns:
        job_id
    """
    job_id = str(uuid.uuid4())
    
    # Register job in database
    execute_insert(
        """INSERT INTO training_jobs 
           (id, dataset_id, model_type, hyperparameters, status)
           VALUES (?, ?, ?, ?, 'QUEUED')""",
        (job_id, dataset_id, model_type, json.dumps(hyperparams))
    )
    
    # Audit log
    execute_insert(
        """INSERT INTO audit_log (event_type, actor, details)
           VALUES (?, ?, ?)""",
        ("JOB_SUBMIT", "api", json.dumps({
            "job_id": job_id,
            "dataset_id": dataset_id,
            "model_type": model_type
        }))
    )
    
    # Enqueue
    job_payload = json.dumps({
        "job_id": job_id,
        "dataset_id": dataset_id,
        "model_type": model_type,
        "hyperparams": hyperparams
    })
    
    if _redis_available and _redis_client:
        _redis_client.rpush(REDIS_QUEUE_NAME, job_payload.encode())
        logger.info(f"Job {job_id} pushed to Redis queue")
    else:
        _fallback_queue.put(job_payload)
        logger.info(f"Job {job_id} pushed to in-process queue")
    
    return job_id


def get_job_status(job_id: str) -> dict | None:
    """Get the current status of a training job."""
    rows = execute_query(
        """SELECT id, dataset_id, model_type, hyperparameters, status,
                  progress, accuracy, loss, started_at, completed_at,
                  error_msg, created_at
           FROM training_jobs WHERE id = ?""",
        (job_id,)
    )
    if not rows:
        return None
    row = rows[0]
    row["hyperparameters"] = json.loads(row.get("hyperparameters", "{}"))
    return row


def list_jobs(limit: int = 50) -> list[dict]:
    """List all training jobs."""
    rows = execute_query(
        """SELECT id, dataset_id, model_type, status, progress,
                  accuracy, loss, created_at, completed_at
           FROM training_jobs ORDER BY created_at DESC LIMIT ?""",
        (limit,)
    )
    return rows


def _update_job(job_id: str, **kwargs):
    """Update job fields."""
    sets = []
    params = []
    for key, val in kwargs.items():
        sets.append(f"{key} = ?")
        params.append(val)
    params.append(job_id)
    
    execute_insert(
        f"UPDATE training_jobs SET {', '.join(sets)} WHERE id = ?",
        tuple(params)
    )


class TrainingWorker:
    """
    Background worker that processes training jobs from the queue.
    """

    def __init__(self):
        _init_redis()
        
        self.key_manager = KeyManager()
        self.vault = DatasetVault(self.key_manager)
        self.registry = ModelRegistry()
        self.sandbox = TrainingSandbox(self.vault, self.registry)
        
        self._running = False
        self._thread: threading.Thread | None = None
        self._active_jobs = 0
        self._lock = threading.Lock()

    def start(self):
        """Start the worker in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Training worker started")

    def stop(self):
        """Stop the worker gracefully."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Training worker stopped")

    def _run_loop(self):
        """Main worker loop — poll queue for jobs."""
        while self._running:
            try:
                if self._active_jobs >= MAX_CONCURRENT_JOBS:
                    time.sleep(1)
                    continue
                
                job_payload = self._dequeue()
                if job_payload:
                    # Run training in a sub-thread for concurrency
                    t = threading.Thread(
                        target=self._process_job,
                        args=(job_payload,),
                        daemon=True
                    )
                    t.start()
                else:
                    time.sleep(1)  # No jobs, wait
                    
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                time.sleep(2)

    def _dequeue(self) -> str | None:
        """Get next job from queue."""
        if _redis_available and _redis_client:
            result = _redis_client.lpop(REDIS_QUEUE_NAME)
            if result:
                return result.decode() if isinstance(result, bytes) else result
            return None
        else:
            try:
                return _fallback_queue.get_nowait()
            except Empty:
                return None

    def _process_job(self, job_payload: str):
        """Process a single training job."""
        with self._lock:
            self._active_jobs += 1
        
        job = json.loads(job_payload)
        job_id = job["job_id"]
        
        try:
            logger.info(f"Starting job {job_id}")
            
            # Update status to RUNNING
            _update_job(
                job_id,
                status="RUNNING",
                started_at=datetime.utcnow().isoformat()
            )
            
            def progress_cb(progress: float, metrics: dict):
                _update_job(
                    job_id,
                    progress=progress,
                    accuracy=metrics.get("val_acc"),
                    loss=metrics.get("val_loss")
                )
            
            # Run secure training
            result = self.sandbox.run_training(
                job_id=job_id,
                dataset_id=job["dataset_id"],
                model_type=job["model_type"],
                hyperparams=job.get("hyperparams", {}),
                progress_callback=progress_cb
            )
            
            # Update job as completed
            _update_job(
                job_id,
                status="COMPLETED",
                progress=1.0,
                accuracy=result["accuracy"],
                loss=result["loss"],
                completed_at=datetime.utcnow().isoformat()
            )
            
            # Audit log
            execute_insert(
                """INSERT INTO audit_log (event_type, actor, details)
                   VALUES (?, ?, ?)""",
                ("JOB_COMPLETE", "worker", json.dumps({
                    "job_id": job_id,
                    "model_id": result["model_id"],
                    "accuracy": result["accuracy"],
                    "duration": result["duration_seconds"]
                }))
            )
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            _update_job(
                job_id,
                status="FAILED",
                error_msg=str(e),
                completed_at=datetime.utcnow().isoformat()
            )
            
            execute_insert(
                """INSERT INTO audit_log (event_type, actor, details)
                   VALUES (?, ?, ?)""",
                ("JOB_FAILED", "worker", json.dumps({
                    "job_id": job_id,
                    "error": str(e)
                }))
            )
        
        finally:
            with self._lock:
                self._active_jobs -= 1
