import os
import shutil
import sys
from pathlib import Path


def place_echo_args(file_path: Path) -> str:
    source = 'D:/Coding/echo-args/build/Debug/echo_args.exe'

    ext = ''
    if sys.platform == 'win32':
        ext = '.exe'

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    dst = Path(file_path).with_suffix(ext)
    shutil.copy(src=source, dst=dst)

    return str(dst).lower().replace('\\', '/')
