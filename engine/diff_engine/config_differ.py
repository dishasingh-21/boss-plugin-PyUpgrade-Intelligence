import difflib
from pathlib import Path
DEFAULT_CONFIG_FILENAMES = ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")

def diff_config_files(old_root: str, new_root: str, filenames: tuple[str, ...] = DEFAULT_CONFIG_FILENAMES) -> dict[str,str]:
    changed = {}
    old_root_path = Path(old_root)
    new_root_path = Path(new_root)
    for filename in filenames:
        old_file = old_root_path / filename
        new_file = new_root_path / filename
        old_text = old_file.read_text(encoding="utf-8") if old_file.exists() else ""
        new_text = new_file.read_text(encoding="utf-8") if new_file.exists() else ""
        if old_text == new_text:
            continue
        diff_lines = difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"old/{filename}",
            tofile=f"new/{filename}",
            lineterm=""
        )
        changed[filename] = "\n".join(diff_lines)
    return changed

