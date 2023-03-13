#!/usr/bin/env python3
import argparse
import pathlib
import sys

from bill_aggregator import consts
from bill_aggregator.exceptions import BillAggConfigError
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
        help=f'bills directory (default: {consts.DEFAULT_WORKDIR})')
    args = parser.parse_args()

    orig_fp = args.conf or consts.DEFAULT_CONFIG_FILE
    config_file = pathlib.Path(orig_fp).absolute()
    if not config_file.is_file():
        print(f'{consts.Color.ERROR}No such file: {orig_fp}{consts.Color.ENDC}')
        sys.exit(1)

    orig_dp = args.dir or consts.DEFAULT_WORKDIR
    workdir = pathlib.Path(orig_dp).absolute()
    if not workdir.is_dir():
        print(f'{consts.Color.ERROR}No such directory: {orig_dp}{consts.Color.ENDC}')
        sys.exit(1)

    # load and validate config file
    conf = config_util.load_yaml_config(file=config_file)
    config_util.ConfigValidator.validate_general_config(conf=conf)

    # actual work begins here
    aggregator = BillAggregator(conf=conf, workdir=workdir)
    aggregator.extract_bills()
    aggregator.aggregate_bills()
    aggregator.export_bills()


if __name__ == '__main__':
    try:
        main()
    except BillAggConfigError as exc:
        print(f'{consts.Color.ERROR}{exc.message}{consts.Color.ENDC}')
        sys.exit(1)
