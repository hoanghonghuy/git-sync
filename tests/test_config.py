import builtins
from argparse import Namespace
from configparser import ConfigParser

import core.config as config
from core.constants import DEFAULT_PROTECTED_BRANCHES, COMMIT_TYPES


def test_initialize_lang_uses_args_lang_and_loads_translations(monkeypatch):
    def fake_load_user_config():
        return ConfigParser()

    monkeypatch.setattr(config, "_load_user_config", fake_load_user_config)

    args = Namespace(lang="en")
    config.initialize_lang(args)

    assert config.LANG == "en"
    # Key tồn tại trong en.json
    text = config.t("start_sync")
    assert isinstance(text, str)
    assert "Git" in text


def test_get_protected_branches_uses_default_when_not_configured(monkeypatch):
    cfg = ConfigParser()

    def fake_load_user_config():
        return cfg

    monkeypatch.setattr(config, "_load_user_config", fake_load_user_config)

    branches = config.get_protected_branches()
    assert branches == {b.strip() for b in DEFAULT_PROTECTED_BRANCHES.split(",")}


def test_get_commit_aliases_reads_from_config(monkeypatch):
    cfg = ConfigParser()
    cfg.add_section("commit_aliases")
    cfg.set("commit_aliases", "ui", "style")
    cfg.set("commit_aliases", "ref", "refactor")

    def fake_load_user_config():
        return cfg

    monkeypatch.setattr(config, "_load_user_config", fake_load_user_config)

    aliases = config.get_commit_aliases()
    assert aliases == {"ui": "style", "ref": "refactor"}


def test_get_commit_types_uses_default_when_not_configured(monkeypatch):
    cfg = ConfigParser()

    def fake_load_user_config():
        return cfg

    monkeypatch.setattr(config, "_load_user_config", fake_load_user_config)

    types = config.get_commit_types()
    assert types == COMMIT_TYPES


def test_get_commit_types_can_be_overridden(monkeypatch):
    cfg = ConfigParser()
    cfg.add_section("settings")
    cfg.set("settings", "commit_types", "feat, fix, ci")

    def fake_load_user_config():
        return cfg

    monkeypatch.setattr(config, "_load_user_config", fake_load_user_config)

    types = config.get_commit_types()
    assert types == ["feat", "fix", "ci"]


def test_get_commit_template_uses_default_when_not_set(monkeypatch):
    cfg = ConfigParser()

    def fake_load_user_config():
        return cfg

    monkeypatch.setattr(config, "_load_user_config", fake_load_user_config)

    template = config.get_commit_template()
    assert "{type}" in template and "{message}" in template


def test_is_auto_ticket_enabled_reads_boolean(monkeypatch):
    cfg = ConfigParser()
    cfg.add_section("settings")
    cfg.set("settings", "auto_ticket_from_branch", "true")

    def fake_load_user_config():
        return cfg

    monkeypatch.setattr(config, "_load_user_config", fake_load_user_config)

    assert config.is_auto_ticket_enabled() is True


def test_get_pre_and_post_hooks(monkeypatch):
    cfg = ConfigParser()
    cfg.add_section("hooks")
    cfg.set("hooks", "pre_sync", "pytest -q")
    cfg.set("hooks", "post_sync", "flake8")

    def fake_load_user_config():
        return cfg

    monkeypatch.setattr(config, "_load_user_config", fake_load_user_config)

    assert config.get_pre_sync_hook() == "pytest -q"
    assert config.get_post_sync_hook() == "flake8"
