import sys

import core.main_flow as main_flow


def test_run_hook_command_success(monkeypatch):
    commands = []

    def fake_run_command(args):
        commands.append(args)
        return 0, ""

    monkeypatch.setattr(main_flow, "run_command", fake_run_command)
    monkeypatch.setattr(main_flow, "t", lambda key, **kw: key)

    main_flow._run_hook_command("echo hello", "pre_sync")

    assert commands == [["echo", "hello"]]


def test_run_hook_command_failure_exits(monkeypatch):
    def fake_run_command(args):
        return 1, ""

    monkeypatch.setattr(main_flow, "run_command", fake_run_command)
    monkeypatch.setattr(main_flow, "t", lambda key, **kw: key)

    try:
        main_flow._run_hook_command("pytest", "pre_sync")
    except SystemExit as exc:
        assert exc.code == 1
    else:  # pragma: no cover
        assert False, "SystemExit was not raised"


def test_run_hook_command_parse_error(monkeypatch):
    monkeypatch.setattr(main_flow, "t", lambda key, **kw: key)

    # Force shlex to raise by passing an invalid posix string (unbalanced quotes)
    try:
        main_flow._run_hook_command("echo 'unterminated", "pre_sync")
    except SystemExit as exc:
        assert exc.code == 1
    else:  # pragma: no cover
        assert False, "SystemExit was not raised"
