DEFAULT_CONFIG_FILE = 'my_bills/config.yaml'
DEFAULT_AGGREGATION = 'result'

RC = 999  # Result column number
MIN_BILL_COLUMNS = 3
WARN_TRIM_ROW_COUNT = 10


class FileType:
    CSV = 'csv'


class AmountFormat:
    ONE_COLUMN_WITH_INDICATORS = 'OneColumnWithIndicators'
    ONE_COLUMN_WITH_SIGN = 'OneColumnWithSign'
