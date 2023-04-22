import argparse
import sys
from typing import List

from .make import make_runner, load_layers_from_all_search_paths


def parse_args(argv: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--layers', nargs='+', required=True, help='Layer files')
    parser.add_argument('-o', '--output', required=True, help='Output .pyz file', type=argparse.FileType('wb'))
    return parser.parse_args(argv)


def main(argv: List[str]):
    args = parse_args(argv)
    layer_contents = load_layers_from_all_search_paths(args.layers)
    make_runner(
        args.output,
        layer_contents=layer_contents,
        additional_script_bases=[],
        additional_search_paths=[]
    )


def run():
    main(sys.argv[1:])


if __name__ == '__main__':
    run()
