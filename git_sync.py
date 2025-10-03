import argparse
import sys

# Import các hàm khởi tạo và hàm chính từ package 'core'
from core.config import initialize_lang
from core.main_flow import start_sync_flow, handle_force_reset # MỚI: import thêm handle_force_reset

def main():
    """Hàm chính của ứng dụng."""
    # --- Thiết lập Argument Parser ---
    parser = argparse.ArgumentParser(description="A smart Git sync tool.")
    
    parser.add_argument("--lang", choices=['en', 'vi'], help="Set the display language (en/vi).")
    
    # argument cho tính năng reset nguy hiểm
    parser.add_argument(
        "--force-reset-to", 
        metavar="REMOTE_BRANCH", 
        help="DANGER: Discard all local changes and force sync to match the remote branch (e.g., origin/main)."
    )

    commit_group = parser.add_mutually_exclusive_group()
    commit_group.add_argument("--feat", metavar="MESSAGE", help='Commit with prefix "feat:"')
    commit_group.add_argument("--fix", metavar="MESSAGE", help='Commit with prefix "fix:"')
    commit_group.add_argument("--chore", metavar="MESSAGE", help='Commit with prefix "chore:"')
    commit_group.add_argument("--refactor", metavar="MESSAGE", help='Commit with prefix "refactor:"')
    commit_group.add_argument("--docs", metavar="MESSAGE", help='Commit with prefix "docs:"')
    commit_group.add_argument("--style", metavar="MESSAGE", help='Commit with prefix "style:"')
    
    args = parser.parse_args()

    # --- Khởi tạo các cài đặt (như ngôn ngữ) ---
    try:
        initialize_lang(args)
    except Exception as e:
        print(f"Failed to initialize settings: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Chạy luồng logic chính ---
    # MỚI: Kiểm tra xem có phải đang chạy lệnh reset không
    if args.force_reset_to:
        handle_force_reset(args.force_reset_to)
    else:
        # Chạy luồng đồng bộ bình thường
        start_sync_flow(args)

if __name__ == "__main__":
    main()