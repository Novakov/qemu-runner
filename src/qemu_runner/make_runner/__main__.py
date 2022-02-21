import argparse

from .make import make_runner, load_layers_from_all_search_paths


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--layers', nargs='+', required=True, help='Layer files')
    parser.add_argument('-o', '--output', required=True, help='Output .pyz file', type=argparse.FileType('wb'))
    return parser.parse_args()


def main(args: argparse.Namespace):
    layer_contents = load_layers_from_all_search_paths(args.layers)
    make_runner(args.output, layer_contents)


if __name__ == '__main__':
    main(parse_args())
