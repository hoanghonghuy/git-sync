import sys

import git_sync


def test_main_maps_alias_to_standard_commit_type(monkeypatch):
    # Giả lập alias ui -> style
    monkeypatch.setattr(
        "core.config.get_commit_aliases",
        lambda: {"ui": "style"},
    )
    called = {}

    def fake_start_sync_flow(args):
        called["args"] = args

    monkeypatch.setattr("core.main_flow.start_sync_flow", fake_start_sync_flow)
    monkeypatch.setattr("core.main_flow.handle_force_reset", lambda a: None)
    monkeypatch.setattr("core.config.initialize_lang", lambda a: None)
    monkeypatch.setattr("core.config.set_language_config", lambda lang: None)

    monkeypatch.setattr(sys, "argv", ["git-sync", "--ui", "Update button"])

    git_sync.main()

    parsed_args = called["args"]
    assert getattr(parsed_args, "style") == "Update button"


def test_main_set_lang_exits_after_updating_config(monkeypatch):
    seen = {}

    def fake_set_lang(lang):
        seen["lang"] = lang

    monkeypatch.setattr("core.config.get_commit_aliases", lambda: {})
    monkeypatch.setattr("core.config.initialize_lang", lambda a: None)
    monkeypatch.setattr("core.config.set_language_config", fake_set_lang)
    monkeypatch.setattr("core.main_flow.start_sync_flow", lambda a: None)
    monkeypatch.setattr("core.main_flow.handle_force_reset", lambda a: None)

    monkeypatch.setattr(sys, "argv", ["git-sync", "--set-lang", "vi"])

    try:
        git_sync.main()
    except SystemExit as exc:
        assert exc.code == 0
        assert seen["lang"] == "vi"
    else:  # pragma: no cover - should not reach here
        assert False, "SystemExit was not raised"
