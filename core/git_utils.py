import subprocess
import sys

def run_command(command, capture=True):
    """Thực thi một lệnh hệ thống và trả về mã lỗi cùng output."""
    try:
        result = subprocess.run(command, check=False, capture_output=capture, text=True, encoding='utf-8')
        is_utility = any(util in " ".join(command) for util in ['git branch', 'git status'])
        if capture and not is_utility:
            if result.stdout: print(result.stdout, end='')
            if result.stderr: print(result.stderr, file=sys.stderr, end='')
        return result.returncode, result.stdout.strip() + result.stderr.strip()
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Is Git installed and in your PATH?", file=sys.stderr)
        return -1, ""
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return -1, ""

def get_current_branch():
    """Lấy tên của branch Git hiện tại."""
    return_code, branch_name = run_command(['git', 'branch', '--show-current'])
    return branch_name if return_code == 0 and branch_name else None