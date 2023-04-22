import os
from os.path import dirname
from pathlib import Path
from typing import Optional, List


def find_qemu(
        engine: str,
        script_paths: Optional[List[str]] = None,
        search_paths: Optional[List[str]] = None
) -> Optional[Path]:
    def find_executable(base_path: Path) -> Optional[Path]:
        exts = os.environ.get('PATHEXT', '').split(os.path.pathsep)
        for e in exts:
            path = base_path / f'{engine}{e}'
            if os.path.exists(path):
                return path
        return None

    if script_paths is None:
        script_paths = [__file__]

    if search_paths is None:
        search_paths = []

    paths_to_check = []

    if 'QEMU_DEV' in os.environ:
        return Path(os.environ['QEMU_DEV'])

    if 'QEMU_DIR' in os.environ:
        paths_to_check.append(os.environ['QEMU_DIR'].rstrip('/').rstrip('\\'))

    paths_to_check += search_paths

    for script_path in script_paths:
        look_at = dirname(script_path)
        while True:
            paths_to_check.append(look_at)
            paths_to_check.append(look_at + '/qemu')
            look_at_next = dirname(look_at)
            if look_at_next == look_at:
                break

            look_at = look_at_next

    paths_to_check.extend(os.environ.get('PATH', '').split(os.pathsep))

    for p in paths_to_check:
        found = find_executable(Path(p))
        if found is not None:
            return found

    return Path(engine)
