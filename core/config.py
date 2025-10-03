import configparser
import json
import locale
import sys  # THÊM DÒNG NÀY ĐỂ SỬA LỖI
from pathlib import Path

# --- Biến toàn cục để lưu trữ ngôn ngữ và các chuỗi dịch ---
LANG = 'en'
_TRANSLATIONS = {}

def load_translations():
    """Tải các chuỗi ngôn ngữ từ file strings.json."""
    global _TRANSLATIONS
    try:
        # Đường dẫn tới thư mục gốc của dự án (đi ngược lên 1 cấp từ thư mục core)
        project_root = Path(__file__).parent.parent
        locales_path = project_root / 'locales' / 'strings.json'
        with open(locales_path, 'r', encoding='utf-8') as f:
            _TRANSLATIONS = json.load(f)
    except FileNotFoundError:
        print("Error: locales/strings.json not found.", file=sys.stderr)
        # Có thể thoát chương trình ở đây nếu muốn
    except json.JSONDecodeError:
        print("Error: Could not decode locales/strings.json.", file=sys.stderr)

def t(key, **kwargs):
    """Hàm thông dịch: lấy chuỗi văn bản theo key và ngôn ngữ đã chọn."""
    message = _TRANSLATIONS.get(key, {}).get(LANG, f"Missing translation for '{key}'")
    return message.format(**kwargs)

def get_system_lang():
    """Lấy mã ngôn ngữ của hệ thống (ví dụ: 'en' hoặc 'vi')."""
    try:
        lang_code, _ = locale.getdefaultlocale()
        return lang_code[:2] if lang_code else 'en'
    except Exception:
        return 'en'

def initialize_lang(args):
    """Xác định ngôn ngữ sẽ sử dụng theo thứ tự ưu tiên."""
    global LANG
    config = _load_user_config()
    
    if args.lang:
        LANG = args.lang
    elif config.has_option('settings', 'language'):
        LANG = config.get('settings', 'language')
    else:
        LANG = get_system_lang()
    
    # Sau khi xác định được LANG, tải các bản dịch
    load_translations()

def get_protected_branches():
    """Lấy danh sách các branch được bảo vệ từ file config."""
    config = _load_user_config()
    fallback_branches = 'main,master,develop'
    protected_str = config.get('settings', 'protected_branches', fallback=fallback_branches)
    return {branch.strip() for branch in protected_str.split(',')}

def _load_user_config():
    """Hàm nội bộ để đọc file .gitsyncrc."""
    config = configparser.ConfigParser()
    project_config_path = Path.cwd() / '.gitsyncrc'
    home_config_path = Path.home() / '.gitsyncrc'
    config.read([home_config_path, project_config_path])
    return config

def get_commit_aliases():
    """Đọc các bí danh của loại commit từ file .gitsyncrc."""
    config = _load_user_config()
    if config.has_section('commit_aliases'):
        # Trả về một dictionary, ví dụ: {'ref': 'refactor', 'test': 'test'}
        return {alias: target for alias, target in config.items('commit_aliases')}
    return {}