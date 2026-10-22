"""Durable, same-run observations for interrupted audits; distinct from response caching."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from ..core.types import ModelResponse


class AuditCheckpoint:
    """Resume only an identical run, retaining completed controls as original observations.

    Response journals contain raw answers needed for scoring. They are private local
    working files, not minimized sharing artifacts. Each completed call is fsynced.
    """
    def __init__(self, directory, prompts, settings, resume=False):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.manifest_path = directory / "run_manifest.json"
        self.responses_path = directory / "responses.private.jsonl"
        signature = hashlib.sha256(json.dumps({"settings": settings, "prompts": [asdict(p) for p in prompts]}, sort_keys=True).encode()).hexdigest()
        if self.manifest_path.exists():
            if not resume:
                raise ValueError("This output directory already contains a run. Use --resume with identical settings or choose a new --output-dir.")
            self.manifest = json.loads(self.manifest_path.read_text())
            if self.manifest.get("signature") != signature:
                raise ValueError("Checkpoint settings, prompts, or installed model digest differ. Choose a new output directory for a new experiment.")
        else:
            if resume:
                raise ValueError("No run manifest exists in this output directory; start a new run without --resume.")
            if self.responses_path.exists():
                raise ValueError("An orphan response journal exists. Choose a new output directory.")
            self.manifest = {"schema_version": 1, "run_id": f"audit_{uuid.uuid4().hex[:12]}",
                             "started_at": time.time(), "signature": signature, "settings": settings,
                             "planned_requests": len(prompts),
                             "privacy_note": "responses.private.jsonl contains raw model answers for local resume; share audit_dataset.json instead."}
            self._write_private(self.manifest_path, json.dumps(self.manifest, indent=2))
        self.allowed_ids = {p.prompt_id for p in prompts}
        self.responses = self._load()

    @staticmethod
    def _write_private(path, content):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())

    def _load(self):
        observations = {}
        if not self.responses_path.exists():
            return observations
        os.chmod(self.responses_path, 0o600)
        with self.responses_path.open("rb+") as stream:
            while True:
                start = stream.tell()
                line = stream.readline()
                if not line:
                    break
                # A killed write can leave a partial final record. The call was not
                # durably completed; retain all prior complete records and retry it.
                if not line.endswith(b"\n"):
                    print("Checkpoint warning: an incomplete final journal record was discarded. That in-flight request may already have run; it will be retried as the same planned observation, not counted as an independent replicate.", flush=True)
                    stream.truncate(start)
                    break
                try:
                    response = ModelResponse(**json.loads(line))
                except (ValueError, TypeError) as error:
                    raise ValueError("Checkpoint has a malformed complete response record; refusing to resume.") from error
                if response.prompt_id not in self.allowed_ids or response.prompt_id in observations:
                    raise ValueError("Checkpoint contains an unknown or duplicate prompt ID; refusing to resume.")
                observations[response.prompt_id] = response
        return observations

    def record(self, response):
        if response.prompt_id not in self.allowed_ids or response.prompt_id in self.responses:
            raise ValueError("Cannot checkpoint an unknown or already completed prompt.")
        fd = os.open(self.responses_path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(response.to_dict()) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.responses[response.prompt_id] = response
