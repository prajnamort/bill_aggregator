#!/usr/bin/env python
import argparse
import pathlib
import yaml

from consts import DEFAULT_CONFIG_FILE


def load_yaml_configs(file=DEFAULT_CONFIG_FILE):
    with open(file, 'r') as f:
        return list(yaml.safe_load_all(f))


def handle_aggregation(conf, workdir):
    print(conf)
    print(workdir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--conf',
        metavar='CONF', 
        required=False,
        help=f'YAML config file (default: {DEFAULT_CONFIG_FILE})')
    parser.add_argument(
        '-d', '--dir',
        metavar='DIR',
        required=False,
        help='bills directory (default: where your CONF file locates)')

    args = parser.parse_args()
    config_file = args.conf or DEFAULT_CONFIG_FILE
    if args.dir:
        workdir = pathlib.Path(args.dir).absolute()
    else:
        workdir = pathlib.Path(config_file).parent.absolute()

    agg_configs = load_yaml_configs(file=config_file)
    for agg_conf in agg_configs:
        handle_aggregation(conf=agg_conf, workdir=workdir)


if __name__ == '__main__':
    main()
