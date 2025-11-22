import subprocess
import sys
from typing import Optional, Sequence, Tuple
from .config import t

DRY_RUN: bool = False

def set_dry_run(enabled: bool) -> None:
    """Bật/tắt chế độ dry-run cho các lệnh git."""
    global DRY_RUN
    DRY_RUN = enabled

def run_command(command: Sequence[str], capture: bool = True) -> Tuple[int, str]:
    """Thực thi một lệnh hệ thống và trả về mã lỗi cùng output."""
    try:
        cmd_str = " ".join(command)
        is_utility = any(util in cmd_str for util in ['git branch', 'git status'])

        # Trong chế độ dry-run, với các lệnh git không phải utility, chỉ in ra mà không thực thi
        if DRY_RUN and command and command[0] == 'git' and not is_utility:
            print(f"[DRY-RUN] {cmd_str}")
            return 0, ""

        result = subprocess.run(command, check=False, capture_output=capture, text=True, encoding='utf-8')
        if capture and not is_utility:
            if result.stdout: print(result.stdout, end='')
            if result.stderr: print(result.stderr, file=sys.stderr, end='')
        return result.returncode, result.stdout.strip() + result.stderr.strip()
    except FileNotFoundError:
        print(t('command_not_found', cmd=command[0]), file=sys.stderr)
        return -1, ""
    except Exception as e:
        print(t('unexpected_error', error=str(e)), file=sys.stderr)
        return -1, ""

def get_current_branch() -> Optional[str]:
    """Lấy tên của branch Git hiện tại."""
    return_code, branch_name = run_command(['git', 'branch', '--show-current'])
    return branch_name if return_code == 0 and branch_name else None