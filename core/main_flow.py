# Tệp: core/main_flow.py

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
    # Danh sách các loại commit chuẩn
    commit_types = ["feat", "fix", "chore", "refactor", "docs", "style", "perf", "test"]
    
    used_commit_type = None
    for c_type in commit_types:
        if getattr(args, c_type, None):
            used_commit_type = c_type
            break

    if used_commit_type:
        scope = f"({args.scope})" if args.scope else ""
        commit_prefix = f"{used_commit_type}{scope}: "
        commit_message = getattr(args, used_commit_type)
    else:
        # Chế độ interactive không thay đổi
        print(t('preparing_commit'))
        commit_message = input(t('commit_prompt'))

    if not commit_message.strip():
        print(t('empty_commit_message'), file=sys.stderr)
        return None
    
    return f"{commit_prefix}{commit_message}"

def execute_sync(commit_message, args):
    """Thực hiện chuỗi lệnh add, commit, push và các tác vụ sau đồng bộ."""
    original_branch = get_current_branch()
    
    print(t('adding_files'))
    run_command(['git', 'add', '.'])

    print(t('committing_with_message', message=commit_message))
    
    print(t('review_changes_header'))
    run_command(['git', 'diff', '--stat', 'HEAD'])
    
    confirmation = input(t('commit_confirm_prompt'))
    if confirmation.lower() not in ['y', 'yes', '']:
        print(t('process_cancelled'))
        sys.exit(0)

    return_code, _ = run_command(['git', 'commit', '-m', commit_message])
    if return_code != 0:
        sys.exit(1)

    print(t('pushing_to_remote'))
    push_return_code, push_output = run_command(['git', 'push'])
    
    if push_return_code == 0:
        print(t('sync_success'))
        _run_post_sync_tasks(args, original_branch)
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
                    _run_post_sync_tasks(args, original_branch)
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
    original_branch = get_current_branch()
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
        print(t('no_changes_to_commit_proceed_pull'))
        run_command(['git', 'pull', '--rebase'])
        if args.update_after:
            _update_target_branch(args.update_after, original_branch)
    elif not output.strip():
        print(t('no_changes'))
        if not was_stashed:
            sys.exit(0)
    else:
        final_commit_message = get_commit_message(args)
        if not final_commit_message:
            sys.exit(1)
        execute_sync(final_commit_message, args)

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

def _run_post_sync_tasks(args, original_branch):
    """Chạy các tác vụ sau khi push thành công, như tạo tag hoặc cập nhật branch."""
    if args.tag:
        tag_name = args.tag
        print(t('creating_tag', tag=tag_name))
        run_command(['git', 'tag', tag_name])
        
        print(t('pushing_tag', tag=tag_name))
        tag_push_code, _ = run_command(['git', 'push', 'origin', tag_name])
        
        if tag_push_code == 0:
            print(t('tag_pushed_successfully', tag=tag_name))
        else:
            print(t('tag_push_failed', tag=tag_name), file=sys.stderr)

    if args.update_after:
        _update_target_branch(args.update_after, original_branch)

def _update_target_branch(target_branch, original_branch):
    """Hàm nội bộ để checkout, pull một branch khác rồi quay lại."""
    if target_branch == original_branch:
        return

    print(t('updating_other_branch_header'))
    
    print(t('switching_to_branch', branch=target_branch))
    checkout_code, _ = run_command(['git', 'checkout', target_branch])
    if checkout_code != 0:
        print(t('update_branch_failed', branch=target_branch), file=sys.stderr)
        run_command(['git', 'checkout', original_branch])
        return

    print(t('pulling_latest_for_branch', branch=target_branch))
    run_command(['git', 'pull', '--rebase'])

    print(t('returning_to_previous_branch', branch=original_branch))
    run_command(['git', 'checkout', original_branch])
    print(t('update_branch_success', branch=target_branch))