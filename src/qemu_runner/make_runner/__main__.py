import argparse

from qemu_runner.layer_locator import load_layer
from .make import make_runner


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--layers', nargs='+', required=True, help='Layer files')
    parser.add_argument('-o', '--output', required=True, help='Output .pyz file', type=argparse.FileType('wb'))
    return parser.parse_args()


def main(args: argparse.Namespace):
    layer_contents = [load_layer(layer, packages=['qemu_runner']) for layer in args.layers]
    make_runner(args.output, layer_contents)


if __name__ == '__main__':
    main(parse_args())
