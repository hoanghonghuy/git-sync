from argparse import Namespace

import core.main_flow as main_flow
from core.constants import COMMIT_TYPES


def test_get_commit_message_with_type_and_scope(monkeypatch):
    args = Namespace(scope="api")
    # Gán giá trị cho một loại commit bất kỳ
    for c in COMMIT_TYPES:
        setattr(args, c, None)
    args.feat = "Implement login"

    message = main_flow.get_commit_message(args)
    assert message == "feat(api): Implement login"


def test_get_commit_message_interactive(monkeypatch):
    args = Namespace(scope=None)
    for c in COMMIT_TYPES:
        setattr(args, c, None)

    monkeypatch.setattr(main_flow, "t", lambda key, **kw: "")
    monkeypatch.setattr("builtins.input", lambda prompt="": "Manual message")

    message = main_flow.get_commit_message(args)
    assert message == "Manual message"


def test_get_commit_message_empty_returns_none(monkeypatch):
    args = Namespace(scope=None)
    for c in COMMIT_TYPES:
        setattr(args, c, None)

    monkeypatch.setattr(main_flow, "t", lambda key, **kw: "")
    monkeypatch.setattr("builtins.input", lambda prompt="": "   ")

    message = main_flow.get_commit_message(args)
    assert message is None


def test_get_commit_message_with_ticket_and_template(monkeypatch):
    args = Namespace(scope="api")
    for c in COMMIT_TYPES:
        setattr(args, c, None)
    args.fix = "Fix bug"

    monkeypatch.setattr(main_flow, "get_commit_types", lambda: COMMIT_TYPES)
    monkeypatch.setattr(main_flow, "get_commit_template", lambda: "[{ticket}] {type}{scope}: {message}")
    monkeypatch.setattr(main_flow, "is_auto_ticket_enabled", lambda: True)
    monkeypatch.setattr(main_flow, "get_current_branch", lambda: "feature/ABC-123-fix-bug")

    message = main_flow.get_commit_message(args)
    assert message == "[ABC-123] fix(api): Fix bug"


def test_handle_force_reset_confirmed_runs_git_commands(monkeypatch):
    commands = []

    def fake_run_command(cmd):
        commands.append(cmd)
        return 0, ""

    monkeypatch.setattr(main_flow, "run_command", fake_run_command)
    monkeypatch.setattr(main_flow, "t", lambda key, **kw: key)
    monkeypatch.setattr("builtins.input", lambda prompt="": "origin/main")

    main_flow.handle_force_reset("origin/main")

    assert commands == [
        ["git", "fetch", "--all"],
        ["git", "reset", "--hard", "origin/main"],
        ["git", "clean", "-df"],
    ]


def test_handle_force_reset_cancelled_exits(monkeypatch):
    monkeypatch.setattr(main_flow, "run_command", lambda cmd: (0, ""))
    monkeypatch.setattr(main_flow, "t", lambda key, **kw: key)
    monkeypatch.setattr("builtins.input", lambda prompt="": "wrong-branch")

    try:
        main_flow.handle_force_reset("origin/main")
    except SystemExit as exc:
        assert exc.code == 0
    else:  # pragma: no cover - should not reach here
        assert False, "SystemExit was not raised"


def test_maybe_stash_changes_sets_flag_correctly(monkeypatch):
    outputs = ["No local changes to save", "Saved working directory state"]

    def fake_run_command(cmd):
        return 0, outputs.pop(0)

    monkeypatch.setattr(main_flow, "run_command", fake_run_command)
    monkeypatch.setattr(main_flow, "t", lambda key, **kw: key)

    args = Namespace(stash=True)
    was_stashed_first = main_flow._maybe_stash_changes(args)
    was_stashed_second = main_flow._maybe_stash_changes(args)

    assert was_stashed_first is False
    assert was_stashed_second is True
