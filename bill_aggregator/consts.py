# Default config
DEFAULT_CONFIG_FILE = 'config.yaml'
DEFAULT_WORKDIR = 'bills/'
DEFAULT_AGGREGATION = 'result'

# Other configs
MIN_BILL_COLUMNS = 3
WARN_TRIM_ROW_COUNT = 10
FINAL_MEMO_SEPARATOR = '; '


# Common macros used across the project
FIELDS = 'fields'
EXT_FIELDS = 'extra_fields'
COL = 'column'
FORMAT = 'format'

ACCT = 'account'
AGG = 'aggregation'
DATE = 'date'
TIME = 'time'
NAME = 'name'
MEMO = 'memo'
AMT = 'amount'
AMT_TYPE = 'amount_type'


class FileType:
    CSV = 'csv'
    XLS = 'xls'

    ALL = [CSV, XLS]


FILE_EXTENSIONS = {
    # lower case only
    FileType.CSV: ['.csv'],
    FileType.XLS: ['.xls'],
}


class AmountFormat:
    ONE_COLUMN_WITH_INDICATORS = 'OneColumnWithIndicators'
    ONE_COLUMN_WITH_SIGN = 'OneColumnWithSign'
    TWO_COLUMNS = 'TwoColumns'

    ALL = [
        ONE_COLUMN_WITH_INDICATORS,
        ONE_COLUMN_WITH_SIGN,
        TWO_COLUMNS,
    ]


class AmountType:
    IN = 'in'
    OUT = 'out'
    UNKNOWN = 'unknown'


class ExportType:
    XLSX = 'xlsx'

    ALL = [XLSX]
