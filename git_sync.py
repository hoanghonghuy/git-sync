import subprocess
import sys
import os
import argparse

TRANSLATIONS = {
    'start_sync': {
        'en': "🚀 Starting Git sync process...",
        'vi': "🚀 Bắt đầu quy trình đồng bộ Git..."
    },
    'not_a_repo': {
        'en': "❌ Error: This directory is not a Git repository. Please run `git init` first.",
        'vi': "❌ Lỗi: Thư mục này không phải là một kho chứa Git. Vui lòng chạy `git init` trước."
    },
    'working_on_branch': {
        'en': "   Working on branch: [{branch}]",
        'vi': "   Đang làm việc trên branch: [{branch}]"
    },
    'branch_warning': {
        'en': "\n⚠️  WARNING: You are about to commit directly to the '{branch}' branch.",
        'vi': "\n⚠️  CẢNH BÁO: Bạn sắp commit trực tiếp vào branch '{branch}'."
    },
    'confirm_prompt': {
        'en': "   This action is not recommended. Are you sure you want to continue? (y/n): ",
        'vi': "   Hành động này không được khuyến khích. Bạn có chắc chắn muốn tiếp tục? (y/n): "
    },
    'process_cancelled': {
        'en': "👍  Process cancelled. Safety first!",
        'vi': "👍  Đã hủy quy trình. An toàn là trên hết!"
    },
    'cannot_determine_branch': {
        'en': "   Could not determine the current branch, please check.",
        'vi': "   Không thể xác định branch hiện tại, vui lòng kiểm tra lại."
    },
    'no_changes': {
        'en': "\n✅ No changes to commit. Everything is up to date.",
        'vi': "\n✅ Không có thay đổi nào để commit. Mọi thứ đã được đồng bộ."
    },
    'adding_files': {
        'en': "\n--- 1. Adding all changes (git add .) ---",
        'vi': "\n--- 1. Đang thêm tất cả các thay đổi (git add .) ---"
    },
    'preparing_commit': {
        'en': "\n--- 2. Preparing commit ---",
        'vi': "\n--- 2. Chuẩn bị commit ---"
    },
    'commit_prompt': {
        'en': "   Enter your commit message: ",
        'vi': "   Nhập vào commit message của bạn: "
    },
    'empty_commit_message': {
        'en': "❌ Commit message cannot be empty. Aborted.",
        'vi': "❌ Commit message không được để trống. Đã hủy."
    },
    'committing_with_message': {
        'en': "   Committing with message: \"{message}\"",
        'vi': "   Chuẩn bị commit với message: \"{message}\""
    },
    'pushing_to_remote': {
        'en': "\n--- 3. Pushing to remote (git push) ---",
        'vi': "\n--- 3. Đang đẩy code lên remote (git push) ---"
    },
    'push_failed': {
        'en': "❌ Error executing `git push`.",
        'vi': "❌ Lỗi khi thực hiện `git push`."
    },
    'non_fast_forward_hint': {
        'en': "\n   Hint: It seems the remote branch has new commits.",
        'vi': "\n   Gợi ý: Có vẻ như branch trên remote đã có commit mới."
    },
    'pull_prompt': {
        'en': "   Do you want to automatically run 'git pull --rebase' and try again? (y/n): ",
        'vi': "   Bạn có muốn tự động chạy 'git pull --rebase' và thử push lại không? (y/n): "
    },
    'pulling_code': {
        'en': "\n--- 4. Pulling new changes (git pull --rebase) ---",
        'vi': "\n--- 4. Đang kéo code mới về (git pull --rebase) ---"
    },
    'retrying_push': {
        'en': "\n--- 5. Retrying push (git push) ---",
        'vi': "\n--- 5. Đang đẩy code lại (git push) ---"
    },
    'sync_after_update_success': {
        'en': "\n✅ Sync successful after update!",
        'vi': "\n✅ Đồng bộ thành công sau khi cập nhật!"
    },
    'pull_failed': {
        'en': "\n❌ `git pull --rebase` failed. There might be conflicts. Please resolve them manually.",
        'vi': "\n❌ `git pull --rebase` thất bại. Có thể có xung đột (conflict). Vui lòng giải quyết thủ công."
    },
    'push_after_pull_failed': {
        'en': "\n❌ Push still failed after pulling. Please check manually.",
        'vi': "\n❌ Vẫn lỗi sau khi pull. Vui lòng kiểm tra thủ công."
    },
    'pull_cancelled': {
        'en': "👍  Cancelled. Please run `git pull` manually before pushing again.",
        'vi': "👍  Đã hủy. Vui lòng `git pull` thủ công trước khi push."
    },
    'sync_success': {
        'en': "\n✅ Sync successful!",
        'vi': "\n✅ Đồng bộ thành công!"
    },
}

LANG = 'en' # Ngôn ngữ mặc định

def t(key, **kwargs):
    """Hàm thông dịch: lấy chuỗi văn bản theo key và ngôn ngữ đã chọn."""
    message = TRANSLATIONS.get(key, {}).get(LANG, f"Missing translation for '{key}'")
    return message.format(**kwargs)

def run_command(command, capture=True):
    try:
        result = subprocess.run(command, check=False, capture_output=capture, text=True, encoding='utf-8')
        is_utility = any(util in " ".join(command) for util in ['git branch', 'git status'])
        if capture and not is_utility:
            if result.stdout: print(result.stdout, end='')
            if result.stderr: print(result.stderr, file=sys.stderr, end='')
        return result.returncode, result.stdout.strip() + result.stderr.strip()
    except FileNotFoundError:
        print(f"Lỗi: Lệnh '{command[0]}' không được tìm thấy. Git đã được cài đặt và thêm vào PATH chưa?", file=sys.stderr)
        return -1, ""
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn: {e}", file=sys.stderr)
        return -1, ""

def get_current_branch():
    return_code, branch_name = run_command(['git', 'branch', '--show-current'])
    return branch_name if return_code == 0 and branch_name else None

def main():
    global LANG
    parser = argparse.ArgumentParser(description=t('start_sync')) # Tạm dùng key này cho description
    
    parser.add_argument("--lang", default='en', choices=['en', 'vi'], help="Set the display language (en/vi).")

    commit_group = parser.add_mutually_exclusive_group()
    commit_group.add_argument("--feat", metavar="MESSAGE", help='Commit with prefix "feat:"')
    commit_group.add_argument("--fix", metavar="MESSAGE", help='Commit with prefix "fix:"')
    commit_group.add_argument("--chore", metavar="MESSAGE", help='Commit with prefix "chore:"')
    commit_group.add_argument("--refactor", metavar="MESSAGE", help='Commit with prefix "refactor:"')
    commit_group.add_argument("--docs", metavar="MESSAGE", help='Commit with prefix "docs:"')
    commit_group.add_argument("--style", metavar="MESSAGE", help='Commit with prefix "style:"')
    
    args = parser.parse_args()
    LANG = args.lang

    print(t('start_sync'))

    if not os.path.isdir('.git'):
        print(t('not_a_repo'), file=sys.stderr)
        sys.exit(1)
        
    current_branch = get_current_branch()
    protected_branches = {'main', 'master', 'develop'}

    if current_branch:
        print(t('working_on_branch', branch=current_branch))
        if current_branch in protected_branches:
            print(t('branch_warning', branch=current_branch))
            confirmation = input(t('confirm_prompt'))
            if confirmation.lower() != 'y':
                print(t('process_cancelled'))
                sys.exit(0)
    else:
        print(t('cannot_determine_branch'), file=sys.stderr)
    
    return_code, output = run_command(['git', 'status', '--porcelain'])
    if not output.strip():
        print(t('no_changes'))
        sys.exit(0)

    print(t('adding_files'))
    run_command(['git', 'add', '.'])

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
        sys.exit(1)
    
    final_commit_message = f"{commit_prefix}{commit_message}"
    print(t('committing_with_message', message=final_commit_message))
    
    return_code, _ = run_command(['git', 'commit', '-m', final_commit_message])
    if return_code != 0: sys.exit(1)

    print(t('pushing_to_remote'))
    push_return_code, push_output = run_command(['git', 'push'])
    
    if push_return_code != 0:
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

    print(t('sync_success'))

if __name__ == "__main__":
    main()