# Default config
DEFAULT_CONFIG_FILE = 'my_bills/config.yaml'
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


class AmountFormat:
    ONE_COLUMN_WITH_INDICATORS = 'OneColumnWithIndicators'
    ONE_COLUMN_WITH_SIGN = 'OneColumnWithSign'


class AmountType:
    IN = 'in'
    OUT = 'out'
    UNKNOWN = 'unknown'
