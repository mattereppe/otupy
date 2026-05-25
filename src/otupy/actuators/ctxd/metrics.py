"""Shared per-call timing instrumentation for CTXD actuators.

Both the Azure (AKS) and the Proxmox actuators issue many remote API
calls during a single discovery cycle. To make it possible to compare
their performance on equal terms — and to feed the numbers into the
thesis evaluation — every API call is timed and written to a dedicated
log file in a single, parser-friendly line format::

    <ISO_TIMESTAMP> INFO API_CALL actuator=<name> label=<tag>
        elapsed_s=<float> success=<bool> bytes_out=<int> cmd=<repr>

At the end of each discovery cycle, an aggregate summary is emitted::

    <ISO_TIMESTAMP> INFO API_SUMMARY actuator=<name> total_calls=<n>
        total_discover_s=<float>
    <ISO_TIMESTAMP> INFO API_SUMMARY actuator=<name> label=<tag>
        count=<n> total_s=<f> avg_s=<f> std_s=<f> var_s2=<f>
        min_s=<f> max_s=<f>

The same module exposes a `MetricsCollector` class that each actuator
instantiates once. The collector is configured from the actuator's YAML
config (the ``metrics:`` block) and exposes a `record()` method for
generic call sites and a `measure()` decorator for actuators that prefer
to wrap their helper methods declaratively (Proxmox style).

This module is intentionally agnostic of any specific actuator: nothing
imported here knows about Azure CLI, kubectl, or proxmoxer.
"""

from __future__ import annotations

import functools
import logging
import time
from math import sqrt
from typing import Any, Callable, Optional

# Single shared logger for every actuator's timing measurements. Each
# MetricsCollector instance can attach its own FileHandler to it (the
# handler is tagged with the destination path so we don't add duplicates
# when multiple actuators happen to point at the same file).
metrics_logger = logging.getLogger("otupy.actuators.ctxd.metrics")
metrics_logger.setLevel(logging.INFO)


def _stats(values: list[float]) -> dict[str, float]:
    """Population-stat summary of a list of floats.

    Population variance (divide by n) is used so that the std of a
    single-sample group is exactly zero rather than undefined. For
    sample variance, switch the denominator to ``n - 1``.
    """
    n = len(values)
    if n == 0:
        return {"count": 0}
    total = sum(values)
    mean = total / n
    var = sum((v - mean) ** 2 for v in values) / n
    return {
        "count": n,
        "total_s": total,
        "avg_s": mean,
        "var_s2": var,
        "std_s": sqrt(var),
        "min_s": min(values),
        "max_s": max(values),
    }


class MetricsCollector:
    """Per-actuator timing collector.

    Construct with the actuator name (used to tag every log line) and the
    ``metrics`` dict read from the actuator's YAML config. Recognized
    config keys are:

      - ``enabled`` (bool, default False): master switch.
      - ``file`` (str, default ``"api_calls.log"``): destination path
        for the dedicated metrics file handler. Relative paths are
        resolved against the connector's current working directory.
      - ``mode`` (str, default ``"a"``): file open mode. ``"a"``
        appends across runs (good for accumulating multi-run datasets);
        ``"w"`` truncates each run.
      - ``propagate`` (bool, default False): if True, metrics records
        are also forwarded to the root logger / console; otherwise they
        stay confined to the metrics file.

    When ``enabled`` is False the collector is a no-op: ``record()``
    silently returns, the decorator returned by ``measure()`` adds no
    overhead beyond a single ``if``-check, and ``log_summary()`` does
    nothing. The collector is therefore safe to wire in unconditionally.
    """

    def __init__(self, actuator_name: str, metrics_cfg: Optional[dict] = None) -> None:
        self.actuator_name = actuator_name
        cfg = metrics_cfg or {}
        self.enabled: bool = bool(cfg.get("enabled", False))
        self._measurements: list[dict[str, Any]] = []
        self._t0: Optional[float] = None

        if self.enabled:
            self._install_file_handler(
                path=cfg.get("file", "api_calls.log"),
                mode=cfg.get("mode", "a"),
                propagate=bool(cfg.get("propagate", False)),
            )

    # ------------------------------------------------------------------
    # Handler management
    # ------------------------------------------------------------------

    @staticmethod
    def _install_file_handler(path: str, mode: str, propagate: bool) -> None:
        """Attach a FileHandler to `metrics_logger`, idempotently.

        Two actuators pointing at the same file share the same handler;
        two actuators pointing at different files each get their own.
        """
        for h in metrics_logger.handlers:
            if (
                getattr(h, "_ctxd_metrics_handler", False)
                and getattr(h, "baseFilename", None) == path
            ):
                metrics_logger.propagate = propagate
                return

        fh = logging.FileHandler(path, mode=mode)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
        fh._ctxd_metrics_handler = True
        metrics_logger.addHandler(fh)
        metrics_logger.propagate = propagate
        logging.getLogger(__name__).info(
            "CTXD metrics will be logged to %s", path,
        )

    # ------------------------------------------------------------------
    # Public API used by the actuators
    # ------------------------------------------------------------------

    def start_run(self) -> None:
        """Mark the beginning of a discovery cycle.

        Clears any previous measurements (so each run's stats are
        independent) and records the start time for the aggregate
        summary.
        """
        if not self.enabled:
            return
        self._measurements.clear()
        self._t0 = time.perf_counter()

    def end_run(self) -> None:
        """Emit the aggregate summary for the current cycle."""
        if not self.enabled or self._t0 is None:
            return
        total_elapsed = time.perf_counter() - self._t0
        self._log_summary(total_elapsed)
        self._t0 = None

    def record(
        self,
        label: str,
        elapsed_s: float,
        *,
        success: bool = True,
        bytes_out: int = 0,
        cmd: str = "",
    ) -> None:
        """Record a single call measurement.

        Called explicitly by actuators that don't decorate (e.g. the
        Azure actuator wraps `_aks_invoke` manually). For actuators
        that decorate, use `measure()` instead.
        """
        if not self.enabled:
            return
        self._measurements.append({
            "label": label,
            "elapsed_s": elapsed_s,
            "success": success,
            "bytes_out": bytes_out,
            "cmd": cmd,
            "timestamp": time.time(),
        })
        metrics_logger.info(
            "API_CALL actuator=%s label=%s elapsed_s=%.6f success=%s "
            "bytes_out=%d cmd=%r",
            self.actuator_name, label, elapsed_s, success, bytes_out, cmd,
        )

    def measure(self, label: Optional[str] = None) -> Callable:
        """Return a decorator that times a function as a single call.

        The returned wrapper always invokes the function; when metrics
        are disabled it adds essentially no overhead. The ``label``
        defaults to the wrapped function's name, which is what Proxmox
        wants for its REST helpers (`get_cluster_nodes`, ...).

        Usage::

            self._metrics = MetricsCollector("ctxd-proxmox", cfg)
            ...
            @self._metrics.measure()
            def get_cluster_nodes(self): ...
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                tag = label or func.__name__
                t_start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.perf_counter() - t_start
                    # Best-effort payload size: works for str/bytes/list/dict;
                    # falls back to 0 for opaque return types.
                    try:
                        bytes_out = (
                            len(result) if hasattr(result, "__len__") else 0
                        )
                    except Exception:
                        bytes_out = 0
                    self.record(
                        tag,
                        elapsed,
                        success=True,
                        bytes_out=bytes_out,
                        cmd=tag,
                    )
                    return result
                except Exception:
                    elapsed = time.perf_counter() - t_start
                    self.record(
                        tag,
                        elapsed,
                        success=False,
                        bytes_out=0,
                        cmd=tag,
                    )
                    raise
            return wrapper
        return decorator

    # ------------------------------------------------------------------
    # Inspection / reporting
    # ------------------------------------------------------------------

    def measurements(self) -> list[dict[str, Any]]:
        """Return a shallow copy of the current run's measurements."""
        return list(self._measurements)

    def _log_summary(self, total_elapsed: float) -> None:
        if not self._measurements:
            metrics_logger.info(
                "API_SUMMARY actuator=%s total_calls=0 total_discover_s=%.3f",
                self.actuator_name, total_elapsed,
            )
            return

        by_label: dict[str, list[float]] = {}
        for m in self._measurements:
            by_label.setdefault(m["label"], []).append(m["elapsed_s"])

        metrics_logger.info(
            "API_SUMMARY actuator=%s total_calls=%d total_discover_s=%.3f",
            self.actuator_name, len(self._measurements), total_elapsed,
        )
        for label, vs in by_label.items():
            s = _stats(vs)
            metrics_logger.info(
                "API_SUMMARY actuator=%s label=%s count=%d total_s=%.3f "
                "avg_s=%.6f std_s=%.6f var_s2=%.6f min_s=%.6f max_s=%.6f",
                self.actuator_name, label,
                s["count"], s["total_s"], s["avg_s"], s["std_s"],
                s["var_s2"], s["min_s"], s["max_s"],
            )

        # Aggregate across all labels (useful for cross-actuator
        # comparison in the thesis).
        all_vs = [m["elapsed_s"] for m in self._measurements]
        s = _stats(all_vs)
        metrics_logger.info(
            "API_SUMMARY actuator=%s label=__all__ count=%d total_s=%.3f "
            "avg_s=%.6f std_s=%.6f var_s2=%.6f min_s=%.6f max_s=%.6f",
            self.actuator_name,
            s["count"], s["total_s"], s["avg_s"], s["std_s"],
            s["var_s2"], s["min_s"], s["max_s"],
        )
