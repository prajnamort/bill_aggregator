import yaml
from schema import Schema, Or, Optional, SchemaError

from bill_aggregator.consts import (
    DEFAULT_CONFIG_FILE, FileType, AmountFormat,
    FIELDS, EXT_FIELDS, COL, FORMAT, ACCT, AGG, DATE, TIME, NAME, MEMO, AMT,
)
from bill_aggregator.exceptions import BillAggregatorException


config_schema = Schema({
    'bill_groups': list,    # bill_group_schema
})


bill_group_schema = Schema({
    ACCT: str,
    Optional(AGG): str,
    'file_type': Or(FileType.CSV, FileType.XLS),
    'file_config': dict,    # specific xxx_file_config_schema
    Optional('final_memo'): [str],
})

tabular_file_config_common = {  # Not a Schema(), don't validate on this
    'has_header': bool,
    FIELDS: {
        DATE: {
            COL: Or(str, int, [Or(str, int)]),
            Optional('dayfirst'): bool,
            Optional('yearfirst'): bool,
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
        AMT: dict,    # specific xxx_amt_schema
    },
    Optional(EXT_FIELDS): {
        str: {
            COL: Or(str, int),
        },
    },
}

csv_file_config_schema = Schema({
    Optional('encoding'): str,
    Optional('delimiter'): str,
    **tabular_file_config_common,
})

xls_file_config_schema = Schema({
    Optional('skiprows'): int,
    Optional('skipfooters'): int,
    **tabular_file_config_common,
})

one_col_with_idcs_amt_schema = Schema({
    FORMAT: AmountFormat.ONE_COLUMN_WITH_INDICATORS,
    COL: Or(str, int),
    'indicators': [{
        COL: Or(str, int),
        'inbound_value': str,
        'outbound_value': str,
    }],
})

one_col_with_sign_amt_schema = Schema({
    FORMAT: AmountFormat.ONE_COLUMN_WITH_SIGN,
    COL: Or(str, int),
    Optional('is_outbound_positive'): bool,
})

two_cols_amt_schema = Schema({
    FORMAT: AmountFormat.TWO_COLUMNS,
    'inbound': {COL: Or(str, int)},
    'outbound': {COL: Or(str, int)},
})


class ConfigValidator:

    @classmethod
    def validate_config(cls, conf):
        try:
            config_schema.validate(conf)
            for bill_group_conf in conf['bill_groups']:
                cls.validate_bill_group_config(bill_group_conf)

            print("Configuration is valid.")
        except SchemaError as se:
            raise se

    @classmethod
    def validate_bill_group_config(cls, bill_group_conf):
        bill_group_schema.validate(bill_group_conf)
        file_type = bill_group_conf['file_type']
        if file_type == FileType.CSV:
            cls.validate_csv_file_config(bill_group_conf['file_config'])
        elif file_type == FileType.XLS:
            cls.validate_xls_file_config(bill_group_conf['file_config'])

    @classmethod
    def validate_csv_file_config(cls, file_conf):
        csv_file_config_schema.validate(file_conf)
        cls.validate_amt_config(file_conf[FIELDS][AMT])

    @classmethod
    def validate_xls_file_config(cls, file_conf):
        xls_file_config_schema.validate(file_conf)
        cls.validate_amt_config(file_conf[FIELDS][AMT])

    @classmethod
    def validate_amt_config(cls, amt_conf):
        if FORMAT not in amt_conf:
            raise BillAggregatorException('format must be specified for amount field')
        amt_format = amt_conf[FORMAT]
        if amt_format == AmountFormat.ONE_COLUMN_WITH_INDICATORS:
            one_col_with_idcs_amt_schema.validate(amt_conf)
        elif amt_format == AmountFormat.ONE_COLUMN_WITH_SIGN:
            one_col_with_sign_amt_schema.validate(amt_conf)
        elif amt_format == AmountFormat.TWO_COLUMNS:
            two_cols_amt_schema.validate(amt_conf)
        else:
            raise BillAggregatorException(f'invalid format for amount field: {amt_format}')


def load_yaml_config(file=DEFAULT_CONFIG_FILE):
    with open(file, 'r') as f:
        return yaml.safe_load(f)
