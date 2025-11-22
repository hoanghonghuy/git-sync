# Tệp: core/main_flow.py

import sys
import os
import re
import shlex
from argparse import Namespace
from typing import Optional
from .config import (
    t,
    get_protected_branches,
    get_commit_types,
    get_commit_template,
    is_auto_ticket_enabled,
    get_pre_sync_hook,
    get_post_sync_hook,
)
from .console import colorize
from .git_utils import run_command, get_current_branch
from .constants import COMMIT_TYPES

def handle_branch_protection(args: Namespace) -> None:
    """Kiểm tra và hỏi xác nhận nếu đang ở trên branch được bảo vệ."""
    current_branch = get_current_branch()
    protected_branches = get_protected_branches()
    
    if not current_branch:
        print(colorize(t('cannot_determine_branch'), 'error'), file=sys.stderr)
        return

    print(colorize(t('working_on_branch', branch=current_branch), 'info'))
    if current_branch in protected_branches:
        print(colorize(t('branch_warning', branch=current_branch), 'warning'))
        if getattr(args, 'yes', False):
            confirmation = 'y'
        else:
            confirmation = input(t('confirm_prompt'))

        if confirmation.lower() != 'y':
            print(colorize(t('process_cancelled'), 'warning'))
            sys.exit(0)

def get_commit_message(args: Namespace) -> Optional[str]:
    """Lấy commit message từ args hoặc từ input của người dùng."""
    commit_message, commit_prefix = "", ""
    # Danh sách các loại commit chuẩn
    commit_types = get_commit_types()
    
    used_commit_type = None
    for c_type in commit_types:
        if getattr(args, c_type, None):
            used_commit_type = c_type
            break

    if used_commit_type:
        scope = f"({args.scope})" if args.scope else ""
        commit_prefix = f"{used_commit_type}{scope}: "
        commit_message = getattr(args, used_commit_type)
        if is_auto_ticket_enabled():
            branch = get_current_branch()
            ticket = _extract_ticket_from_branch(branch)
        else:
            ticket = ""

        template = get_commit_template()
        data = {
            'type': used_commit_type,
            'scope': scope,
            'message': commit_message,
            'ticket': ticket,
        }
        try:
            return template.format(**data)
        except Exception:
            # Fallback về định dạng cũ nếu template bị lỗi
            pass

    else:
        # Chế độ interactive không thay đổi
        print(colorize(t('preparing_commit'), 'info'))
        commit_message = input(t('commit_prompt'))

    if not commit_message.strip():
        print(colorize(t('empty_commit_message'), 'error'), file=sys.stderr)
        return None
    
    return f"{commit_prefix}{commit_message}"

def _extract_ticket_from_branch(branch_name: Optional[str]) -> str:
    if not branch_name:
        return ""
    match = re.search(r"[A-Z]+-\d+", branch_name)
    if match:
        return match.group(0)
    return ""

def execute_sync(commit_message: str, args: Namespace) -> None:
    """Thực hiện chuỗi lệnh add, commit, push và các tác vụ sau đồng bộ."""
    original_branch = get_current_branch()
    
    _stage_and_commit_changes(commit_message, args)
    _push_and_handle_remote(args, original_branch)

def _stage_and_commit_changes(commit_message: str, args: Namespace) -> None:
    print(colorize(t('adding_files'), 'info'))
    run_command(['git', 'add', '.'])

    print(colorize(t('committing_with_message', message=commit_message), 'info'))
    
    print(colorize(t('review_changes_header'), 'info'))
    run_command(['git', 'diff', '--stat', 'HEAD'])
    
    if getattr(args, 'yes', False):
        confirmation = ''
    else:
        confirmation = input(t('commit_confirm_prompt'))

    if confirmation.lower() not in ['y', 'yes', '']:
        print(colorize(t('process_cancelled'), 'warning'))
        sys.exit(0)

    return_code, _ = run_command(['git', 'commit', '-m', commit_message])
    if return_code != 0:
        sys.exit(1)

def _push_and_handle_remote(args: Namespace, original_branch: Optional[str]) -> None:
    print(colorize(t('pushing_to_remote'), 'info'))
    push_return_code, push_output = run_command(['git', 'push'])
    
    if push_return_code == 0:
        print(colorize(t('sync_success'), 'success'))
        _run_post_sync_tasks(args, original_branch)
        return

    if "rejected" in push_output and "non-fast-forward" in push_output:
        print(colorize(t('non_fast_forward_hint'), 'warning'))
        if getattr(args, 'yes', False):
            pull_confirmation = 'y'
        else:
            pull_confirmation = input(t('pull_prompt'))

        if pull_confirmation.lower() == 'y':
            print(colorize(t('pulling_code'), 'info'))
            pull_return_code, _ = run_command(['git', 'pull', '--rebase'])
            if pull_return_code == 0:
                print(colorize(t('retrying_push'), 'info'))
                retry_push_code, _ = run_command(['git', 'push'])
                if retry_push_code == 0:
                    print(colorize(t('sync_after_update_success'), 'success'))
                    _run_post_sync_tasks(args, original_branch)
                    sys.exit(0)
                else:
                    print(colorize(t('push_after_pull_failed'), 'error'), file=sys.stderr)
            else:
                print(colorize(t('pull_failed'), 'error'), file=sys.stderr)
        else:
            print(colorize(t('pull_cancelled'), 'warning'))
    else:
        print(colorize(t('push_failed'), 'error'), file=sys.stderr)
    
    sys.exit(1)
    
def start_sync_flow(args: Namespace) -> None:
    """Hàm chính điều phối toàn bộ luồng đồng bộ."""
    original_branch = get_current_branch()
    was_stashed = _maybe_stash_changes(args)
            
    print(colorize(t('start_sync'), 'info'))

    if not os.path.isdir('.git'):
        print(colorize(t('not_a_repo'), 'error'), file=sys.stderr)
        sys.exit(1)
        
    handle_branch_protection(args)
    _run_pre_sync_hook_if_needed()
    
    _handle_status_and_sync(args, was_stashed, original_branch)

    _apply_stash_if_needed(was_stashed)

def _maybe_stash_changes(args: Namespace) -> bool:
    was_stashed = False

    if args.stash:
        print(colorize(t('stashing_changes'), 'info'))
        _, stash_output = run_command(['git', 'stash', 'push', '-m', 'git-sync auto-stash'])
        
        if "No local changes to save" in stash_output:
            print(colorize(t('no_changes_to_stash'), 'info'))
        else:
            was_stashed = True
            print(colorize(t('stashed_successfully'), 'success'))
    return was_stashed

def _handle_status_and_sync(args: Namespace, was_stashed: bool, original_branch: Optional[str]) -> None:
    _, output = run_command(['git', 'status', '--porcelain'])
    if not output.strip() and was_stashed:
        print(colorize(t('no_changes_to_commit_proceed_pull'), 'info'))
        run_command(['git', 'pull', '--rebase'])
        if args.update_after:
            _update_target_branch(args.update_after, original_branch)
    elif not output.strip():
        print(colorize(t('no_changes'), 'info'))
        if not was_stashed:
            # Không có thay đổi nào: kết thúc sớm nhưng không ném SystemExit,
            # để caller (CLI) có thể thoát tự nhiên với exit code 0.
            return

    else:
        final_commit_message = get_commit_message(args)
        if not final_commit_message:
            sys.exit(1)
        execute_sync(final_commit_message, args)

def _apply_stash_if_needed(was_stashed: bool) -> None:
    if not was_stashed:
        return

    print(colorize(t('popping_stash'), 'info'))
    pop_code, _ = run_command(['git', 'stash', 'pop'])
    if pop_code != 0:
        print(colorize(t('stash_pop_conflict'), 'warning'), file=sys.stderr)
    else:
        print(colorize(t('stash_pop_success'), 'success'))
            
def handle_force_reset(branch_to_reset: str) -> None:
    """Thực hiện reset branch local một cách an toàn."""
    print("\n" + "="*60)
    print(colorize(t('force_reset_warning_header'), 'warning'))
    print(t('force_reset_warning_line1'))
    print(t('force_reset_warning_line2', branch=branch_to_reset))
    print(t('force_reset_warning_line3'))
    print("="*60)
    
    prompt = t('force_reset_prompt', branch=branch_to_reset)
    confirmation = input(prompt)

    if confirmation.strip() == branch_to_reset:
        print(colorize(f"\n✅ {t('force_reset_confirmed')}", 'success'))
        
        print(colorize(f"\n--- 1. {t('force_reset_step1')}", 'info'))
        run_command(['git', 'fetch', '--all'])
        
        print(colorize(f"\n--- 2. {t('force_reset_step2', branch=branch_to_reset)}", 'info'))
        run_command(['git', 'reset', '--hard', branch_to_reset])
        
        print(colorize(f"\n--- 3. {t('force_reset_step3')}", 'info'))
        run_command(['git', 'clean', '-df'])
        
        print(colorize(f"\n✅ {t('force_reset_success', branch=branch_to_reset)}", 'success'))
    else:
        print(colorize(f"\n❌ {t('force_reset_cancelled')}", 'warning'))
        sys.exit(0)

def _run_post_sync_tasks(args: Namespace, original_branch: Optional[str]) -> None:
    """Chạy các tác vụ sau khi push thành công, như tạo tag hoặc cập nhật branch."""
    if args.tag:
        tag_name = args.tag
        print(colorize(t('creating_tag', tag=tag_name), 'info'))
        run_command(['git', 'tag', tag_name])
        
        print(colorize(t('pushing_tag', tag=tag_name), 'info'))
        tag_push_code, _ = run_command(['git', 'push', 'origin', tag_name])
        
        if tag_push_code == 0:
            print(colorize(t('tag_pushed_successfully', tag=tag_name), 'success'))
        else:
            print(colorize(t('tag_push_failed', tag=tag_name), 'error'), file=sys.stderr)

    if args.update_after:
        _update_target_branch(args.update_after, original_branch)

    _run_post_sync_hook_if_needed()

def _update_target_branch(target_branch: str, original_branch: Optional[str]) -> None:
    """Hàm nội bộ để checkout, pull một branch khác rồi quay lại."""
    if target_branch == original_branch:
        return

    print(colorize(t('updating_other_branch_header'), 'info'))
    
    print(colorize(t('switching_to_branch', branch=target_branch), 'info'))
    checkout_code, _ = run_command(['git', 'checkout', target_branch])
    if checkout_code != 0:
        print(colorize(t('update_branch_failed', branch=target_branch), 'error'), file=sys.stderr)
        run_command(['git', 'checkout', original_branch])
        return

    print(colorize(t('pulling_latest_for_branch', branch=target_branch), 'info'))
    run_command(['git', 'pull', '--rebase'])

    print(colorize(t('returning_to_previous_branch', branch=original_branch), 'info'))
    run_command(['git', 'checkout', original_branch])
    print(colorize(t('update_branch_success', branch=target_branch), 'success'))

def _run_pre_sync_hook_if_needed() -> None:
    cmd = get_pre_sync_hook()
    if not cmd:
        return
    _run_hook_command(cmd, 'pre_sync')

def _run_post_sync_hook_if_needed() -> None:
    cmd = get_post_sync_hook()
    if not cmd:
        return
    _run_hook_command(cmd, 'post_sync')

def _run_hook_command(cmd_str: str, hook_name: str) -> None:
    try:
        args = shlex.split(cmd_str)
    except ValueError:
        print(colorize(t('hook_parse_error', hook=hook_name), 'error'), file=sys.stderr)
        sys.exit(1)

    print(colorize(t('running_hook', hook=hook_name, command=cmd_str), 'info'))
    code, _ = run_command(args)
    if code != 0:
        print(colorize(t('hook_failed', hook=hook_name), 'error'), file=sys.stderr)
        sys.exit(code)