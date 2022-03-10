import os
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Dict, Optional, Union


def place_echo_args(file_path: Path) -> str:
    if sys.platform == 'win32':
        ext = '.cmd'
    else:
        ext = ''

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    dst = Path(file_path).with_suffix(ext)

    with open(dst, 'w') as f:
        if sys.platform == 'win32':
            f.write(f'@"{sys.executable}" -c "import sys; print(\'\\n\'.join(sys.argv[1:]))" %0 %*')
        else:
            f.write("""#!/bin/sh
echo $(realpath $0)
for i; do 
   echo $i 
done
            """)
            os.fchmod(f.fileno(), 0o755)

    return str(dst).lower().replace('\\', '/')


@contextmanager
def with_env(envs: Dict[str, Optional[Union[str, os.PathLike]]]) -> Iterable[None]:
    prev_values: Dict[str, Optional[str]] = {}
    for k, v in envs.items():
        prev_values[k] = os.environ.get(k, None)

        if v is None:
            if k in os.environ:
                del os.environ[k]
        else:
            os.environ[k] = str(v)

    try:
        yield
    finally:
        for k, v in prev_values.items():
            if v is None:
                if k in os.environ:
                    del os.environ[k]
            else:
                os.environ[k] = v


@contextmanager
def with_cwd(path: Path) -> Iterable[None]:
    prev = os.getcwd()
    try:
        os.makedirs(path, exist_ok=True)
        os.chdir(path)
        yield
    finally:
        os.chdir(prev)


@contextmanager
def with_pypath(*path: Path) -> Iterable[None]:
    prev = list(sys.path)
    try:
        sys.path = [*map(str, path), *sys.path]
        yield
    finally:
        sys.path = prev


@contextmanager
def unload_module_on_exit(*module_name: str) -> Iterable[None]:
    try:
        yield
    finally:
        for m in module_name:
            if m in sys.modules:
                del sys.modules[m]


def place_file(path: Path, content: str) -> Path:
    os.makedirs(path.parent, exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

    return path
