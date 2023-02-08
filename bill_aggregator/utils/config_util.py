import yaml

from bill_aggregator import consts


def load_yaml_config(file=consts.DEFAULT_CONFIG_FILE):
    with open(file, 'r') as f:
        return yaml.safe_load(f)


def check_config(conf, workdir):
    pass
