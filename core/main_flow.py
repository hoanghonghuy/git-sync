import sys
import os
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
    was_stashed = False

    if args.stash:
        print(t('stashing_changes'))
        _, stash_output = run_command(['git', 'stash', 'push', '-m', 'git-sync auto-stash'])
        
        if "No local changes to save" in stash_output:
            print(t('no_changes_to_stash'))
        else:
            was_stashed = True
            print(t('stashed_successfully'))
            
    print(t('start_sync'))

    if not os.path.isdir('.git'):
        print(t('not_a_repo'), file=sys.stderr)
        sys.exit(1)
        
    handle_branch_protection()
    
    _, output = run_command(['git', 'status', '--porcelain'])
    if not output.strip() and was_stashed:
        print("\n✅ No changes to commit, proceeding to pull updates.")
        run_command(['git', 'pull', '--rebase'])
    elif not output.strip():
        print(t('no_changes'))
        if not was_stashed:
            sys.exit(0)
    else:
        final_commit_message = get_commit_message(args)
        if not final_commit_message:
            sys.exit(1)
        execute_sync(final_commit_message)

    if was_stashed:
        print(t('popping_stash'))
        pop_code, _ = run_command(['git', 'stash', 'pop'])
        if pop_code != 0:
            print(t('stash_pop_conflict'), file=sys.stderr)
        else:
            print(t('stash_pop_success'))
            
def handle_force_reset(branch_to_reset):
    """Thực hiện reset branch local một cách an toàn."""
    print("\n" + "="*60)
    print(t('force_reset_warning_header'))
    print(t('force_reset_warning_line1'))
    print(t('force_reset_warning_line2', branch=branch_to_reset))
    print(t('force_reset_warning_line3'))
    print("="*60)
    
    prompt = t('force_reset_prompt', branch=branch_to_reset)
    confirmation = input(prompt)

    if confirmation.strip() == branch_to_reset:
        print(f"\n✅ {t('force_reset_confirmed')}")
        
        print(f"\n--- 1. {t('force_reset_step1')} ---")
        run_command(['git', 'fetch', '--all'])
        
        print(f"\n--- 2. {t('force_reset_step2', branch=branch_to_reset)} ---")
        run_command(['git', 'reset', '--hard', branch_to_reset])
        
        print(f"\n--- 3. {t('force_reset_step3')} ---")
        run_command(['git', 'clean', '-df'])
        
        print(f"\n✅ {t('force_reset_success', branch=branch_to_reset)}")
    else:
        print(f"\n❌ {t('force_reset_cancelled')}")
        sys.exit(0)