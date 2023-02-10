import yaml
from schema import Schema, Or, Optional, SchemaError

from bill_aggregator.consts import (
    DEFAULT_CONFIG_FILE, FileType,
    FIELDS, EXT_FIELDS, COL, DATE, TIME, NAME, MEMO, AMT,
)


def load_yaml_config(file=DEFAULT_CONFIG_FILE):
    with open(file, 'r') as f:
        return yaml.safe_load(f)


class ConfigValidator:
    config_schema = Schema({
        'bill_groups': list,    # bill_group_schema
    })

    bill_group_schema = Schema({
        'account': str,
        Optional('aggregation'): str,
        'file_type': Or(FileType.CSV),
        'file_config': dict,    # csv_file_config_schema
        Optional('final_memo'): [str],
    })

    csv_file_config_schema = Schema({
        Optional('encoding'): str,
        'has_header': bool,
        FIELDS: {
            DATE: {
                COL: Or(str, int),
                Optional('date_order'): str,
            },
            Optional(TIME): {
                COL: Or(str, int),
            },
            NAME: {
                COL: Or(str, int),
            },
            Optional(MEMO): {
                COL: Or(str, int),
            },
            AMT: dict,    # amount_schema
        },
        Optional(EXT_FIELDS): {
            str: {
                COL: Or(str, int),
            },
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
        if file_type == FileType.CSV:
            cls.validate_csv_file_config(bill_group_conf['file_config'])

    @classmethod
    def validate_csv_file_config(cls, file_conf):
        cls.csv_file_config_schema.validate(file_conf)
