import configparser
import json
import locale
import sys  # THÊM DÒNG NÀY ĐỂ SỬA LỖI
from pathlib import Path
from argparse import Namespace
from typing import Any, Dict, Optional, Set
from .constants import DEFAULT_PROTECTED_BRANCHES, COMMIT_TYPES

# --- Biến toàn cục để lưu trữ ngôn ngữ và các chuỗi dịch ---
LANG: str = 'en'
_TRANSLATIONS: Dict[str, Any] = {}
DEFAULT_COMMIT_TEMPLATE: str = "{type}{scope}: {message}"

def load_translations() -> None:
    """Tải các chuỗi ngôn ngữ từ các file locale."""
    global _TRANSLATIONS
    # Đường dẫn tới thư mục gốc của dự án (đi ngược lên 1 cấp từ thư mục core)
    project_root = Path(__file__).parent.parent
    locales_dir = project_root / 'locales'
    lang_file = locales_dir / f"{LANG}.json"
    fallback_file = locales_dir / 'strings.json'

    try:
        if lang_file.exists():
            with open(lang_file, 'r', encoding='utf-8') as f:
                _TRANSLATIONS = json.load(f)
        elif fallback_file.exists():
            with open(fallback_file, 'r', encoding='utf-8') as f:
                _TRANSLATIONS = json.load(f)
        else:
            print("Error: No locale files found in 'locales' directory.", file=sys.stderr)
            _TRANSLATIONS = {}
    except json.JSONDecodeError:
        print("Error: Could not decode locale file.", file=sys.stderr)
        _TRANSLATIONS = {}

def t(key: str, **kwargs: Any) -> str:
    """Hàm thông dịch: lấy chuỗi văn bản theo key và ngôn ngữ đã chọn."""
    entry = _TRANSLATIONS.get(key)
    if isinstance(entry, dict):
        message = entry.get(LANG, f"Missing translation for '{key}'")
    elif isinstance(entry, str):
        message = entry
    else:
        message = f"Missing translation for '{key}'"
    return message.format(**kwargs)

def get_system_lang() -> str:
    """Lấy mã ngôn ngữ của hệ thống (ví dụ: 'en' hoặc 'vi')."""
    try:
        lang_code, _ = locale.getdefaultlocale()
        return lang_code[:2] if lang_code else 'en'
    except Exception:
        return 'en'

def initialize_lang(args: Namespace) -> None:
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

def get_protected_branches() -> Set[str]:
    """Lấy danh sách các branch được bảo vệ từ file config."""
    config = _load_user_config()
    fallback_branches = DEFAULT_PROTECTED_BRANCHES
    protected_str = config.get('settings', 'protected_branches', fallback=fallback_branches)
    return {branch.strip() for branch in protected_str.split(',')}

def get_commit_types() -> list[str]:
    """Lấy danh sách các loại commit, có thể override qua config."""
    config = _load_user_config()
    if config.has_option('settings', 'commit_types'):
        raw = config.get('settings', 'commit_types')
        types = [c.strip() for c in raw.split(',') if c.strip()]
        return types or COMMIT_TYPES
    return COMMIT_TYPES

def get_commit_template() -> str:
    """Lấy template commit message từ config hoặc dùng mặc định."""
    config = _load_user_config()
    return config.get('settings', 'commit_template', fallback=DEFAULT_COMMIT_TEMPLATE)

def is_auto_ticket_enabled() -> bool:
    """Kiểm tra cờ tự động lấy ticket từ tên branch."""
    config = _load_user_config()
    try:
        return config.getboolean('settings', 'auto_ticket_from_branch', fallback=False)
    except ValueError:
        return False

def _load_user_config() -> configparser.ConfigParser:
    """Hàm nội bộ để đọc file .gitsyncrc."""
    cfg = configparser.ConfigParser()
    project_config_path = Path.cwd() / '.gitsyncrc'
    home_config_path = Path.home() / '.gitsyncrc'
    cfg.read([home_config_path, project_config_path])
    return cfg

def get_pre_sync_hook() -> Optional[str]:
    """Lấy lệnh pre_sync hook (nếu có) từ file config."""
    config = _load_user_config()
    cmd = config.get('hooks', 'pre_sync', fallback='').strip()
    return cmd or None

def get_post_sync_hook() -> Optional[str]:
    """Lấy lệnh post_sync hook (nếu có) từ file config."""
    config = _load_user_config()
    cmd = config.get('hooks', 'post_sync', fallback='').strip()
    return cmd or None

def get_commit_aliases() -> Dict[str, str]:
    """Đọc các bí danh của loại commit từ file .gitsyncrc."""
    config = _load_user_config()
    if config.has_section('commit_aliases'):
        # Trả về một dictionary, ví dụ: {'ref': 'refactor', 'test': 'test'}
        return {alias: target for alias, target in config.items('commit_aliases')}
    return {}

def set_language_config(lang: str) -> None:
    """Ghi đè cài đặt ngôn ngữ vào file .gitsyncrc global."""
    home_config_path = Path.home() / '.gitsyncrc'
    config = configparser.ConfigParser()
    
    # Đọc file config hiện có (nếu có)
    config.read(home_config_path)
    
    # Đảm bảo section [settings] tồn tại
    if not config.has_section('settings'):
        config.add_section('settings')
        
    # Đặt giá trị ngôn ngữ mới
    config.set('settings', 'language', lang)
    
    # Ghi lại toàn bộ file config
    with open(home_config_path, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
        
    print(t('set_lang_success', lang=lang.upper()))