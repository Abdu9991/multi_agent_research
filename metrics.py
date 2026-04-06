from statistics import mean
from typing import Any


def evaluate(runs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    runs = runs or []
    total_runs = len(runs)
    completed_runs = [run for run in runs if run.get("status") == "completed"]
    failed_runs = [run for run in runs if run.get("status") == "failed"]

    success_rate = (len(completed_runs) / total_runs * 100) if total_runs else 0.0

    informative_results = [run for run in completed_runs if (run.get("result_preview") or "").strip()]
    consistency_rate = (len(informative_results) / len(completed_runs) * 100) if completed_runs else 0.0

    grouped_attempts: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        key = (run.get("problem") or "").strip().lower()
        if key:
            grouped_attempts.setdefault(key, []).append(run)

    recovery_candidates = 0
    recovered_cases = 0
    for attempts in grouped_attempts.values():
        statuses = [attempt.get("status") for attempt in attempts]
        if "failed" in statuses:
            recovery_candidates += 1
            first_failure = statuses.index("failed")
            if "completed" in statuses[first_failure + 1:]:
                recovered_cases += 1

    if recovery_candidates:
        error_recovery_rate = recovered_cases / recovery_candidates * 100
    else:
        error_recovery_rate = 100.0 if total_runs else 0.0

    durations = [int(run.get("duration_ms", 0)) for run in completed_runs if str(run.get("duration_ms", "")).isdigit()]
    average_duration = round(mean(durations), 2) if durations else 0.0

    return {
        "total_runs": total_runs,
        "completed_runs": len(completed_runs),
        "failed_runs": len(failed_runs),
        "task_success_rate": f"{success_rate:.1f}%",
        "reasoning_consistency": f"{consistency_rate:.1f}%",
        "error_recovery": f"{error_recovery_rate:.1f}%",
        "efficiency": "No completed runs yet" if not durations else f"{average_duration} ms average runtime",
    }
