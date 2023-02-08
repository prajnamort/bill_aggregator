#!/usr/bin/env python
import argparse
import pathlib

from bill_aggregator import consts
from bill_aggregator import exceptions
from bill_aggregator.utils import config_util
from bill_aggregator.aggregator import BillAggregator


def main():
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--conf',
        required=False,
        help=f'YAML config file (default: {consts.DEFAULT_CONFIG_FILE})')
    parser.add_argument(
        '-d', '--dir',
        required=False,
        help='bills directory (default: where your CONF file locates)')
    args = parser.parse_args()

    config_file = pathlib.Path(args.conf or consts.DEFAULT_CONFIG_FILE).absolute()
    if not config_file.is_file():
        raise exceptions.BillAggregatorException(f'{config_file}: no such file')

    if args.dir:
        workdir = pathlib.Path(args.dir).absolute()
    else:
        workdir = config_file.parent
    if not workdir.is_dir():
        raise exceptions.BillAggregatorException(f'{workdir}: no such directory')

    # load and validate config file
    conf = config_util.load_yaml_config(file=config_file)
    config_util.ConfigValidator.validate_config(conf=conf)

    # actual work begins here
    aggregator = BillAggregator(conf=conf, workdir=workdir)
    aggregator.aggregate()


if __name__ == '__main__':
    main()
