from types import SimpleNamespace

import core.git_utils as git_utils


def test_run_command_success(monkeypatch):
    def fake_run(command, check, capture_output, text, encoding):
        return SimpleNamespace(returncode=0, stdout="out\n", stderr="err\n")

    monkeypatch.setattr(git_utils, "subprocess", SimpleNamespace(run=fake_run))

    code, output = git_utils.run_command(["echo", "hello"])
    assert code == 0
    assert output == "outerr"


def test_run_command_file_not_found(monkeypatch):
    class FakeSubprocess:
        def run(self, *args, **kwargs):  # pragma: no cover - replaced by exception
            raise FileNotFoundError()

    monkeypatch.setattr(git_utils, "subprocess", FakeSubprocess())
    monkeypatch.setattr(git_utils, "t", lambda key, **kw: key)

    code, output = git_utils.run_command(["git"])
    assert code == -1
    assert output == ""


def test_run_command_unexpected_error(monkeypatch):
    class FakeSubprocess:
        def run(self, *args, **kwargs):  # pragma: no cover - replaced by exception
            raise RuntimeError("boom")

    monkeypatch.setattr(git_utils, "subprocess", FakeSubprocess())
    monkeypatch.setattr(git_utils, "t", lambda key, **kw: key)

    code, output = git_utils.run_command(["git"])
    assert code == -1
    assert output == ""
