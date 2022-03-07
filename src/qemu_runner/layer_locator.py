import os
import pkgutil
from typing import Optional, Iterable, List


class LayerNotFoundError(Exception):
    pass


def find_layer_file(layer: str, dirs: List[str]) -> Optional[str]:
    possible_files = (os.path.join(base_dir, layer) for base_dir in dirs)

    for p in possible_files:
        if os.path.exists(p):
            with open(p, 'r') as f:
                return f.read()

    return None


def find_layer_package(layer: str, packages: List[str]) -> Optional[str]:
    for pkg in packages:
        try:
            data = pkgutil.get_data(pkg, f'layers/{layer}')
            if data is not None:
                return data.decode('utf-8')
        except FileNotFoundError:
            continue
        except OSError:
            continue

    return None


def flatten_environ_dirs(environ_names: List[str]) -> Iterable[str]:
    for name in environ_names:
        for d in os.environ.get(name, '').split(os.pathsep):
            yield d


def load_layer(
        layer: str,
        *,
        packages: Optional[List[str]] = None,
        search_dir: Optional[List[os.PathLike]] = None,
        environ_names: Optional[List[str]] = None
) -> str:
    packages = packages or []
    search_dir = search_dir or []
    environ_names = environ_names or []

    if os.path.isabs(layer):
        with open(layer, 'r') as f:
            return f.read()

    layer_content = find_layer_file(layer, [os.getcwd()])
    if layer_content is not None:
        return layer_content

    layer_content = find_layer_file(layer, search_dir)
    if layer_content is not None:
        return layer_content

    layer_content = find_layer_file(layer, list(flatten_environ_dirs(environ_names)))
    if layer_content is not None:
        return layer_content

    layer_content = find_layer_package(layer, packages)
    if layer_content is not None:
        return layer_content

    raise LayerNotFoundError(f'Failed to find layer {layer}')
