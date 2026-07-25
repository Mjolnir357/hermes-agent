"""Portable-archive contract for machine/process-scoped Hermes state."""

from __future__ import annotations


RUNTIME_STATE_FILENAMES: frozenset[str] = frozenset(
    {
        "gateway.pid",
        "gateway_state.json",
        "cron.pid",
        "gateway.lock",
        "processes.json",
    }
)
