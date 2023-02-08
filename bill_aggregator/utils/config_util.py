import yaml
from schema import Schema, Or, Optional, SchemaError

from bill_aggregator import consts


def load_yaml_config(file=consts.DEFAULT_CONFIG_FILE):
    with open(file, 'r') as f:
        return yaml.safe_load(f)


class ConfigValidator:
    config_schema = Schema({
        'bill_groups': list,    # bill_group_schema
    })

    bill_group_schema = Schema({
        'account': str,
        Optional('aggregation'): str,
        'file_type': Or('csv'),
        'file_config': dict,    # csv_file_config_schema
        Optional('final_memo'): [str],
    })

    csv_file_config_schema = Schema({
        Optional('encoding'): str,
        'header': bool,
        'fields': {
            'date': str,
            'name': str,
            Optional('memo'): str,
            'amount': dict,    # amount_schema
        },
        'extra_fields': {
            str: str,
        },
    })

    @classmethod
    def validate_config(cls, conf):
        try:
            cls.config_schema.validate(conf)
            for bill_group_conf in conf['bill_groups']:
                cls.validate_bill_group_config(bill_group_conf)

            print("Configuration is valid.")
        except SchemaError as se:
            raise se

    @classmethod
    def validate_bill_group_config(cls, bill_group_conf):
        cls.bill_group_schema.validate(bill_group_conf)
        file_type = bill_group_conf['file_type']
        if file_type == 'csv':
            cls.validate_csv_file_config(bill_group_conf['file_config'])

    @classmethod
    def validate_csv_file_config(cls, file_conf):
        cls.csv_file_config_schema.validate(file_conf)
