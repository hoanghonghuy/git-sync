import sys
import os
# Import các hàm cần thiết từ các module anh em
from .config import t, get_protected_branches
from .git_utils import run_command, get_current_branch

def handle_branch_protection():
    """Kiểm tra và hỏi xác nhận nếu đang ở trên branch được bảo vệ."""
    current_branch = get_current_branch()
    protected_branches = get_protected_branches()
    
    if not current_branch:
        print(t('cannot_determine_branch'), file=sys.stderr)
        return

    print(t('working_on_branch', branch=current_branch))
    if current_branch in protected_branches:
        print(t('branch_warning', branch=current_branch))
        confirmation = input(t('confirm_prompt'))
        if confirmation.lower() != 'y':
            print(t('process_cancelled'))
            sys.exit(0)

def get_commit_message(args):
    """Lấy commit message từ args hoặc từ input của người dùng."""
    commit_message, commit_prefix = "", ""
    if args.feat: commit_prefix, commit_message = "feat: ", args.feat
    elif args.fix: commit_prefix, commit_message = "fix: ", args.fix
    elif args.chore: commit_prefix, commit_message = "chore: ", args.chore
    elif args.refactor: commit_prefix, commit_message = "refactor: ", args.refactor
    elif args.docs: commit_prefix, commit_message = "docs: ", args.docs
    elif args.style: commit_prefix, commit_message = "style: ", args.style
    else:
        print(t('preparing_commit'))
        commit_message = input(t('commit_prompt'))

    if not commit_message.strip():
        print(t('empty_commit_message'), file=sys.stderr)
        return None
    
    return f"{commit_prefix}{commit_message}"

def execute_sync(commit_message):
    """Thực hiện chuỗi lệnh add, commit, push và xử lý lỗi."""
    print(t('adding_files'))
    run_command(['git', 'add', '.'])

    print(t('committing_with_message', message=commit_message))
    return_code, _ = run_command(['git', 'commit', '-m', commit_message])
    if return_code != 0:
        sys.exit(1)

    print(t('pushing_to_remote'))
    push_return_code, push_output = run_command(['git', 'push'])
    
    if push_return_code == 0:
        print(t('sync_success'))
        return

    if "rejected" in push_output and "non-fast-forward" in push_output:
        print(t('non_fast_forward_hint'))
        pull_confirmation = input(t('pull_prompt'))
        if pull_confirmation.lower() == 'y':
            print(t('pulling_code'))
            pull_return_code, _ = run_command(['git', 'pull', '--rebase'])
            if pull_return_code == 0:
                print(t('retrying_push'))
                retry_push_code, _ = run_command(['git', 'push'])
                if retry_push_code == 0:
                    print(t('sync_after_update_success'))
                    sys.exit(0)
                else:
                    print(t('push_after_pull_failed'), file=sys.stderr)
            else:
                print(t('pull_failed'), file=sys.stderr)
        else:
            print(t('pull_cancelled'))
    else:
        print(t('push_failed'), file=sys.stderr)
    
    sys.exit(1)

def start_sync_flow(args):
    """Hàm chính điều phối toàn bộ luồng đồng bộ."""
    print(t('start_sync'))

    if not os.path.isdir('.git'):
        print(t('not_a_repo'), file=sys.stderr)
        sys.exit(1)
        
    handle_branch_protection()
    
    _, output = run_command(['git', 'status', '--porcelain'])
    if not output.strip():
        print(t('no_changes'))
        sys.exit(0)

    final_commit_message = get_commit_message(args)
    if not final_commit_message:
        sys.exit(1)

    execute_sync(final_commit_message)