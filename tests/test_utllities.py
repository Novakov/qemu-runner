import os
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Dict, Optional


def place_echo_args(file_path: Path) -> str:
    source = 'D:/Coding/echo-args/build/Debug/echo_args.exe'

    ext = ''
    if sys.platform == 'win32':
        ext = '.exe'

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    dst = Path(file_path).with_suffix(ext)
    shutil.copy(src=source, dst=dst)

    return str(dst).lower().replace('\\', '/')


@contextmanager
def with_env(envs: Dict[str, Optional[str]]) -> Iterable[None]:
    prev_values: Dict[str, Optional[str]] = {}
    for k, v in envs.items():
        prev_values[k] = os.environ.get(k, None)

        if v is None:
            if k in os.environ:
                del os.environ[k]
        else:
            os.environ[k] = v

    try:
        yield
    finally:
        for k, v in prev_values.items():
            if v is None:
                if k in os.environ:
                    del os.environ[k]
            else:
                os.environ[k] = v
