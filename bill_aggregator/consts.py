import colorama


# Default inputs
DEFAULT_CONFIG_FILE = 'config.yaml'
DEFAULT_WORKDIR = 'bills/'
# Default aggregations (output file names)
RESULTS_DIR = 'results/'
DEFAULT_AGG = 'RESULT'
DEFAULT_SEP_CUR_AGG = 'NO_CURRENCY'

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
CUR = 'currency'
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


# Output and logs
colorama.just_fix_windows_console()


class Color:
    BOLD = colorama.Style.BRIGHT
    HEADER = BOLD + colorama.Fore.MAGENTA
    OKCYAN = colorama.Fore.CYAN
    OKGREEN = colorama.Fore.GREEN
    OKWHITE = colorama.Fore.WHITE
    WARN = colorama.Fore.YELLOW
    ERROR = colorama.Fore.RED
    ENDC = colorama.Style.RESET_ALL

    def disable(self):
        self.BOLD = ''
        self.HEADER = ''
        self.OKCYAN = ''
        self.OKGREEN = ''
        self.WARN = ''
        self.ERROR = ''
        self.ENDC = ''


class LogLevel:
    ERROR = 40
    WARN = 30
    INFO = 20

    ALL = [INFO, WARN, ERROR]
    DEFAULT = INFO
    NONE = 0


class ExtractLoggerScope:
    GROUP = 'bill_group'
    FILE = 'bill_file'

    ALL = [GROUP, FILE]


class ExtractLoggerField:
    ACCT = 'account'
    FILE = 'file'
    ROWS = 'rows'
    SKIP_ROWS = 'skip_rows'
    MSG = 'message'

    GROUP_ALL = [ACCT, MSG]
    FILE_ALL = [FILE, ROWS, SKIP_ROWS, MSG]
