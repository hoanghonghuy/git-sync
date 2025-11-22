import subprocess
import sys

import pytest

import git_sync


@pytest.mark.skipif(subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0, reason="git is required for integration tests")
def test_integration_basic_sync_dry_run(tmp_path, monkeypatch):
    """Smoke test: chạy git-sync trong một repo Git tạm với --dry-run và -y."""
    def run(cmd):
        subprocess.run(cmd, cwd=tmp_path, check=True, capture_output=True, text=True)

    # Khởi tạo repo tạm
    run(["git", "init"])
    run(["git", "config", "user.name", "Test User"])
    run(["git", "config", "user.email", "test@example.com"])

    # Tạo commit đầu tiên để có branch hiện tại rõ ràng
    (tmp_path / "file.txt").write_text("content", encoding="utf-8")
    run(["git", "add", "file.txt"])
    run(["git", "commit", "-m", "init"])

    # Chạy git-sync ở chế độ dry-run + auto-yes
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["git-sync", "--feat", "Integration dry run", "-y", "--dry-run"])

    # Nếu có lỗi sẽ raise exception / SystemExit != 0 làm test fail
    git_sync.main()
