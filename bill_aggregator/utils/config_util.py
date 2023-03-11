import yaml
from schema import Schema, Or, Optional, SchemaError

from bill_aggregator.consts import (
    DEFAULT_CONFIG_FILE, FileType, AmountFormat, ExportType,
    FIELDS, EXT_FIELDS, COL, FORMAT, ACCT, CUR, DATE, TIME, NAME, MEMO, AMT,
)
from bill_aggregator.exceptions import BillAggregatorException


config_schema = Schema({
    'bill_groups': list,    # bill_group_schema
    Optional('separate_by_currency'): bool,
    'export_to': Or(ExportType.XLSX),
    'export_config': dict,    # one of export_config_schemas
})

bill_group_schema = Schema({
    ACCT: str,
    Optional(CUR): str,
    'file_type': str,
    'file_config': dict,    # one of file_config_schemas
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
        AMT: dict,    # one of amount_config_schemas
    },
    Optional(EXT_FIELDS): {
        str: {
            COL: Or(str, int),
        },
    },
}

file_config_schemas = {
    FileType.CSV: Schema({
        Optional('encoding'): str,
        Optional('delimiter'): str,
        **tabular_file_config_common,
    }),
    FileType.XLS: Schema({
        Optional('skiprows'): int,
        Optional('skipfooters'): int,
        **tabular_file_config_common,
    }),
}

amount_config_schemas = {
    AmountFormat.ONE_COLUMN_WITH_INDICATORS: Schema({
        FORMAT: AmountFormat.ONE_COLUMN_WITH_INDICATORS,
        COL: Or(str, int),
        'indicators': [{
            COL: Or(str, int),
            'inbound_value': str,
            'outbound_value': str,
        }],
    }),
    AmountFormat.ONE_COLUMN_WITH_SIGN: Schema({
        FORMAT: AmountFormat.ONE_COLUMN_WITH_SIGN,
        COL: Or(str, int),
        Optional('is_outbound_positive'): bool,
    }),
    AmountFormat.TWO_COLUMNS: Schema({
        FORMAT: AmountFormat.TWO_COLUMNS,
        'inbound': {COL: Or(str, int)},
        'outbound': {COL: Or(str, int)},
    })
}

export_config_schemas = {
    ExportType.XLSX: Schema({
        Optional('font_size'): int,
        Optional('row_height'): int,
        Optional('table_style'): str,
        'columns': list,    # column_config_schema
    }),
}

column_config_schema = Schema({
    'header': str,
    'data': dict,
    Optional('style'): dict,
})


class ConfigValidator:

    @classmethod
    def validate_config(cls, conf):
        try:
            config_schema.validate(conf)

            # validate config for reading original files
            for bill_group_conf in conf['bill_groups']:
                cls.validate_bill_group_config(bill_group_conf)

            # validate config for exporting results
            export_type = conf['export_to']
            if export_type not in ExportType.ALL:
                raise BillAggregatorException(f'invalid export type: {export_type}')
            cls.validate_export_config(export_type, conf['export_config'])

            # print("Configuration is valid.")
        except SchemaError as se:
            raise se

    @classmethod
    def validate_bill_group_config(cls, bill_group_conf):
        bill_group_schema.validate(bill_group_conf)
        file_type = bill_group_conf['file_type']
        if file_type not in FileType.ALL:
            raise BillAggregatorException(f'invalid file_type: {file_type}')

        file_conf = bill_group_conf['file_config']
        if file_type in [FileType.CSV, FileType.XLS]:
            # validation for tabular files
            file_config_schemas[file_type].validate(file_conf)
            cls.validate_amount_config(file_conf[FIELDS][AMT])

    @classmethod
    def validate_amount_config(cls, amt_conf):
        if FORMAT not in amt_conf:
            raise BillAggregatorException('format must be specified for amount field')
        amt_format = amt_conf[FORMAT]
        if amt_format not in AmountFormat.ALL:
            raise BillAggregatorException(f'invalid format for amount field: {amt_format}')
        amount_config_schemas[amt_format].validate(amt_conf)

    @classmethod
    def validate_export_config(cls, export_type, export_conf):
        export_config_schemas[export_type].validate(export_conf)
        for column_config in export_conf['columns']:
            column_config_schema.validate(column_config)


def load_yaml_config(file=DEFAULT_CONFIG_FILE):
    with open(file, 'r') as f:
        return yaml.safe_load(f)
