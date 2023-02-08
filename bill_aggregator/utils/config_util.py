import yaml

from bill_aggregator import consts
from bill_aggregator import exceptions


def load_yaml_configs(file=consts.DEFAULT_CONFIG_FILE):
    with open(file, 'r') as f:
        return list(yaml.safe_load_all(f))


def check_configs(confs, workdir):
    # check subdirs
    if len(confs) > 1:  # multiple aggregations
        subdirs = []
        for conf in confs:
            if 'sub_directory' not in conf:
                raise exceptions.BillAggregatorException('sub_directory must be specified since you have multiple aggregations')
            if conf['sub_directory'] in subdirs:
                raise exceptions.BillAggregatorException(f'{conf["sub_directory"]}: sub_directory duplicated')
            subdirs.append(conf['sub_directory'])
    for conf in confs:
        if 'sub_directory' in conf:
            if conf['sub_directory'] == consts.DEFAULT_AGG_NAME:
                raise exceptions.BillAggregatorException(f'sub_directory cannot be named "{consts.DEFAULT_AGG_NAME}"')
            subdir = workdir / conf['sub_directory']
            if not subdir.is_dir():
                raise exceptions.BillAggregatorException(f'{subdir}: no such directory')
