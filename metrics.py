import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_MAX_RUNS = 50
_RUNS_FILE = Path(__file__).with_name("runs.json")
_runs: deque[dict[str, Any]] = deque(maxlen=_MAX_RUNS)
_next_id = 1


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _load_runs() -> None:
	global _next_id

	if not _RUNS_FILE.exists():
		return

	try:
		content = json.loads(_RUNS_FILE.read_text(encoding="utf-8"))
		if not isinstance(content, list):
			return
		for run in content[-_MAX_RUNS:]:
			if isinstance(run, dict):
				_runs.append(run)
		if _runs:
			_next_id = max(int(run.get("id", 0)) for run in _runs) + 1
	except Exception:
		# Ignore bad or partial files and continue with in-memory tracking.
		return


def _save_runs() -> None:
	_RUNS_FILE.write_text(json.dumps(list(_runs), indent=2), encoding="utf-8")


def record_run(
	problem: str,
	status: str,
	duration_ms: int,
	error: str | None = None,
	result_text: str | None = None,
) -> dict[str, Any]:
	global _next_id

	run = {
		"id": _next_id,
		"timestamp": _utc_now_iso(),
		"problem": problem,
		"status": status,
		"duration_ms": duration_ms,
		"error": error,
		"result_preview": (result_text or "")[:220],
	}
	_next_id += 1
	_runs.append(run)
	_save_runs()
	return run


def get_recent_runs(limit: int = 10, status: str | None = None, query: str | None = None) -> list[dict[str, Any]]:
	safe_limit = max(1, min(limit, _MAX_RUNS))
	runs = list(_runs)
	runs.reverse()

	if status:
		runs = [run for run in runs if str(run.get("status", "")).lower() == status.lower()]

	if query:
		q = query.strip().lower()
		if q:
			runs = [
				run
				for run in runs
				if q in str(run.get("problem", "")).lower() or q in str(run.get("result_preview", "")).lower()
			]

	return runs[:safe_limit]


_load_runs()
