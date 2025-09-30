# D:\workspace\tools\git-sync\git_sync.py
import subprocess
import sys
import os
import argparse

def run_command(command, capture=True):
    """Chạy một lệnh trong terminal và trả về (return_code, output)."""
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=capture,
            text=True,
            encoding='utf-8'
        )
        if capture:
            # Chỉ in output/error nếu không phải lệnh lấy tên branch
            if "git branch --show-current" not in " ".join(command):
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
            return result.returncode, result.stdout.strip() + result.stderr.strip()
        return result.returncode, ""
    except FileNotFoundError:
        print(f"Lỗi: Lệnh '{command[0]}' không được tìm thấy. Git đã được cài đặt và thêm vào PATH chưa?", file=sys.stderr)
        return -1, ""
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn: {e}", file=sys.stderr)
        return -1, ""

def get_current_branch():
    """Lấy tên của branch hiện tại."""
    return_code, branch_name = run_command(['git', 'branch', '--show-current'])
    if return_code == 0 and branch_name:
        return branch_name
    return None

def main():
    parser = argparse.ArgumentParser(description="Tự động hóa quy trình git add, commit, và push.")
    commit_group = parser.add_mutually_exclusive_group()
    commit_group.add_argument("--feat", metavar="MESSAGE", help='Commit với tiền tố "feat:" (tính năng mới)')
    commit_group.add_argument("--fix", metavar="MESSAGE", help='Commit với tiền tố "fix:" (sửa lỗi)')
    commit_group.add_argument("--chore", metavar="MESSAGE", help='Commit với tiền tố "chore:" (việc vặt, bảo trì)')
    commit_group.add_argument("--refactor", metavar="MESSAGE", help='Commit với tiền tố "refactor:" (tái cấu trúc code)')
    commit_group.add_argument("--docs", metavar="MESSAGE", help='Commit với tiền tố "docs:" (cập nhật tài liệu)')
    commit_group.add_argument("--style", metavar="MESSAGE", help='Commit với tiền tố "style:" (chỉnh sửa định dạng code)')
    args = parser.parse_args()

    print("🚀 Bắt đầu quy trình đồng bộ Git...")

    if not os.path.isdir('.git'):
        print("❌ Lỗi: Thư mục này không phải là một kho chứa Git.", file=sys.stderr)
        sys.exit(1)
        
    # --- KIỂM TRA BRANCH ---
    current_branch = get_current_branch()
    protected_branches = {'main', 'master', 'develop'} # Các branch cần bảo vệ

    if current_branch:
        print(f"   Đang làm việc trên branch: [{current_branch}]")
        if current_branch in protected_branches:
            print(f"\n⚠️  CẢNH BÁO: Bạn sắp commit trực tiếp vào branch '{current_branch}'.")
            confirmation = input("   Hành động này không được khuyến khích. Bạn có chắc chắn muốn tiếp tục? (y/n): ")
            if confirmation.lower() != 'y':
                print("👍  Đã hủy quy trình. An toàn là trên hết!")
                sys.exit(0)
    else:
        print("   Không thể xác định branch hiện tại, vui lòng kiểm tra lại.", file=sys.stderr)
    # --- KẾT THÚC ---

    return_code, output = run_command(['git', 'status', '--porcelain'])
    if not output.strip():
        print("✅ Không có thay đổi nào để commit. Mọi thứ đã được đồng bộ.")
        sys.exit(0)

    print("\n--- 1. Đang thêm tất cả các thay đổi (git add .) ---")
    run_command(['git', 'add', '.'])

    commit_prefix = ""
    commit_message = ""
    # logic xử lý commit message 
    if args.feat:
        commit_prefix, commit_message = "feat: ", args.feat
    elif args.fix:
        commit_prefix, commit_message = "fix: ", args.fix
    elif args.chore:
        commit_prefix, commit_message = "chore: ", args.chore
    elif args.refactor:
        commit_prefix, commit_message = "refactor: ", args.refactor
    elif args.docs:
        commit_prefix, commit_message = "docs: ", args.docs
    elif args.style:
        commit_prefix, commit_message = "style: ", args.style
    else:
        print("\n--- 2. Chuẩn bị commit ---")
        commit_message = input("   Nhập vào commit message của bạn: ")

    if not commit_message.strip():
        print("❌ Commit message không được để trống. Đã hủy.", file=sys.stderr)
        sys.exit(1)
    
    final_commit_message = f"{commit_prefix}{commit_message}"
    print(f"   Chuẩn bị commit với message: \"{final_commit_message}\"")
    
    return_code, _ = run_command(['git', 'commit', '-m', final_commit_message])
    if return_code != 0:
        print("❌ Lỗi khi thực hiện `git commit`", file=sys.stderr)
        sys.exit(1)

    print("\n--- 3. Đang đẩy code lên remote (git push) ---")
    return_code, output = run_command(['git', 'push'])
    if return_code != 0:
        print("❌ Lỗi khi thực hiện `git push`.", file=sys.stderr)
        if "rejected" in output and "non-fast-forward" in output:
            print("   Gợi ý: Có vẻ như branch trên remote đã có commit mới. Hãy thử `git pull` trước khi push lại.", file=sys.stderr)
        sys.exit(1)

    print("\n✅ Đồng bộ thành công!")

if __name__ == "__main__":
    main()