"""Regression tests for context-local cron working directories."""

import contextvars
import threading


def test_session_cwd_context_does_not_leak_between_threads(tmp_path, monkeypatch):
    from agent.runtime_cwd import resolve_context_cwd
    from gateway.session_context import clear_session_vars, set_session_vars

    interactive_dir = tmp_path / "interactive"
    interactive_dir.mkdir()
    cron_dir = tmp_path / "cron"
    cron_dir.mkdir()
    monkeypatch.setenv("TERMINAL_CWD", str(interactive_dir))

    cron_ready = threading.Event()
    release_cron = threading.Event()
    observed = {}

    def cron_context():
        tokens = set_session_vars(cwd=str(cron_dir))
        try:
            observed["cron"] = resolve_context_cwd()
            cron_ready.set()
            release_cron.wait(timeout=5)
        finally:
            clear_session_vars(tokens)

    context = contextvars.copy_context()
    thread = threading.Thread(target=context.run, args=(cron_context,))
    thread.start()
    assert cron_ready.wait(timeout=5)

    # A gateway turn running concurrently keeps the process-level interactive
    # cwd; only the copied cron Context sees the job directory.
    observed["interactive"] = resolve_context_cwd()
    release_cron.set()
    thread.join(timeout=5)

    assert not thread.is_alive()
    assert observed == {
        "cron": cron_dir,
        "interactive": interactive_dir,
    }


def test_clear_session_vars_restores_prior_context(tmp_path, monkeypatch):
    from agent.runtime_cwd import resolve_context_cwd
    from gateway.session_context import clear_session_vars, set_session_vars

    interactive_dir = tmp_path / "interactive"
    interactive_dir.mkdir()
    cron_dir = tmp_path / "cron"
    cron_dir.mkdir()
    monkeypatch.setenv("TERMINAL_CWD", str(interactive_dir))

    tokens = set_session_vars(cwd=str(cron_dir))
    assert resolve_context_cwd() == cron_dir
    clear_session_vars(tokens)
    assert resolve_context_cwd() == interactive_dir
