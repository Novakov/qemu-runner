import os
import pkgutil
from typing import Optional


def find_layer_file(layer: str, dirs: list[str]) -> Optional[str]:
    possible_files = (os.path.join(base_dir, layer) for base_dir in dirs)

    for p in possible_files:
        if os.path.exists(p):
            with open(p, 'r') as f:
                return f.read()

    return None


def find_layer_package(layer: str, packages: list[str]) -> Optional[str]:
    for pkg in packages:
        data = pkgutil.get_data(pkg, f'layers/{layer}')
        if data is not None:
            return data.decode('utf-8')

    return None


def load_layer(
        layer: str,
        *,
        packages: Optional[list[str]] = None,
        search_dir: Optional[list[str]] = None,
        environ_names: Optional[list[str]] = None
) -> str:
    packages = packages or []
    search_dir = search_dir or []
    environ_names = environ_names or []

    if os.path.isabs(layer):
        return layer

    layer_content = find_layer_file(layer, [os.getcwd()])
    if layer_content is not None:
        return layer_content

    layer_content = find_layer_package(layer, packages)
    if layer_content is not None:
        return layer_content

    # TODO: custom search dir
    # TODO: environment variables

    raise RuntimeError(f'Failed to find layer {layer}')
