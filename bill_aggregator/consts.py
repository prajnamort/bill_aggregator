DEFAULT_CONFIG_FILE = 'my_bills/config.yaml'
DEFAULT_AGGREGATION = 'result'

MIN_BILL_COLUMNS = 3
WARN_TRIM_ROW_COUNT = 10


class FileType:
    CSV = 'csv'


class AmountFormat:
    OneColumnWithIndicators = 'OneColumnWithIndicators'
    OneColumnWithSign = 'OneColumnWithSign'
