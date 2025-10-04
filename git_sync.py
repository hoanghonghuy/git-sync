import argparse
import sys

# Import các hàm từ package 'core'
from core.config import initialize_lang, get_commit_aliases, set_language_config
from core.main_flow import start_sync_flow, handle_force_reset

def main():
    """Hàm chính của ứng dụng."""
    parser = argparse.ArgumentParser(description="A smart Git sync tool.")
    
    # Đọc alias trước để tự động thêm cờ
    aliases = get_commit_aliases()
    alias_to_target = {alias: target for alias, target in aliases.items()}

    # --- Thiết lập các cờ (flags) ---
    parser.add_argument("--lang", choices=['en', 'vi'], help="Temporarily set the display language for this run.")
    
    parser.add_argument("--set-lang", choices=['en', 'vi'], help="Permanently set the default language in the global config file.")
    
    parser.add_argument(
        "--force-reset-to", 
        metavar="REMOTE_BRANCH", 
        help="DANGER: Discard all local changes and force sync to match the remote branch (e.g., origin/main)."
    )
    
    parser.add_argument(
        "--stash",
        action="store_true",
        help="Automatically stash uncommitted changes before syncing and pop them after."
    )
    
    parser.add_argument(
        "--tag",
        metavar="TAG_NAME",
        help="Create and push a tag after a successful sync (e.g., v1.0.0)."
    )

    parser.add_argument(
        "--update-after",
        metavar="BRANCH_NAME",
        help="After a successful sync, switch to this branch, pull, and switch back."
    )

    commit_group = parser.add_mutually_exclusive_group()
    # Các loại commit chuẩn
    standard_commits = ["feat", "fix", "chore", "refactor", "docs", "style", "perf", "test"]
    for commit_type in standard_commits:
        commit_group.add_argument(f"--{commit_type}", metavar="MESSAGE", help=f'Commit with prefix "{commit_type}:"')
    
    # Tự động thêm các cờ alias vào parser
    for alias, target in alias_to_target.items():
        if alias not in standard_commits: # Tránh thêm lại các cờ đã có
            commit_group.add_argument(
                f"--{alias}",
                metavar="MESSAGE",
                help=f'Alias for "{target}:"'
            )

    args = parser.parse_args()

    # --- Chuyển đổi giá trị từ alias sang cờ chuẩn ---
    for alias, target in alias_to_target.items():
        alias_value = getattr(args, alias, None)
        if alias_value:
            setattr(args, target, alias_value)
            # Không break vì cần getattr để lấy value, không ảnh hưởng logic
    
    # --- Khởi tạo và chạy ứng dụng ---
    try:
        # Luôn phải khởi tạo để có hàm t() cho các thông báo
        initialize_lang(args)
    except Exception as e:
        print(f"Failed to initialize settings: {e}", file=sys.stderr)
        sys.exit(1)

    # Ưu tiên xử lý --set-lang và thoát
    if args.set_lang:
        set_language_config(args.set_lang)
        sys.exit(0)

    # Các luồng logic chính
    if args.force_reset_to:
        handle_force_reset(args.force_reset_to)
    else:
        start_sync_flow(args)

if __name__ == "__main__":
    main()