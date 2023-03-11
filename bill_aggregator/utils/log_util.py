from bill_aggregator.consts import (
    LogLevel, ExtractLoggerScope, ExtractLoggerField, Color,
)
from bill_aggregator.exceptions import BillAggBaseException, BillAggException
from bill_aggregator.utils.string_util import fit_string, Align


class LogData:

    def __init__(self, value=None, level=LogLevel.DEFAULT):
        self.value = value
        self.level = level

    def __bool__(self):
        if self.value is None:
            return False
        return True


class ExtractLogger:
    """Logger for Extracting data from bill files.

    self.data: [
        {
            'account': ...,
            'messages': [...],
            'files': [
                {
                    'file': ...,
                    'rows': ...,
                    'skip_rows': ...,
                    'messages': [...],
                    'ended': False,
                },
                ...  # list of file_data
            ],
            'ended': False,
        },
        ...  # list of group_data
    ]
    """

    GRP_WD = 20
    FILE_WD = 30
    ROWS_WD = 5
    MSG_WD = 60
    LINE_FORMAT = '{grp_str}   {file_str}   {rows_str}   {msg_str}'

    def __init__(self):
        self.data = []
        self.header_printed = False

    def _new_group_data(self):
        return {
            'account': LogData(),
            'messages': [],
            'files': [],
            'ended': False,
        }

    def _new_file_data(self):
        return {
            'file': LogData(),
            'rows': LogData(),
            'skip_rows': LogData(),
            'messages': [],
            'ended': False,
        }

    def _last_or_new_group_data(self):
        if len(self.data) == 0 or self.data[-1]['ended']:
            self.data.append(self._new_group_data())
        return self.data[-1]

    def _last_or_new_file_data(self):
        group_data = self._last_or_new_group_data()
        if len(group_data['files']) == 0 or group_data['files'][-1]['ended']:
            group_data['files'].append(self._new_file_data())
        return group_data['files'][-1]

    def _log_group_data(self, field, value, level):
        assert field in ExtractLoggerField.GROUP_ALL
        assert level in LogLevel.ALL

        group_data = self._last_or_new_group_data()
        if field == ExtractLoggerField.ACCT:
            group_data['account'] = LogData(value=value, level=level)
        elif field == ExtractLoggerField.MSG:
            group_data['messages'].append(LogData(value=value, level=level))

    def _log_file_data(self, field, value, level):
        assert field in ExtractLoggerField.FILE_ALL
        assert level in LogLevel.ALL

        file_data = self._last_or_new_file_data()
        if field == ExtractLoggerField.FILE:
            file_data['file'] = LogData(value=value, level=level)
        elif field == ExtractLoggerField.ROWS:
            file_data['rows'] = LogData(value=value, level=level)
        elif field == ExtractLoggerField.SKIP_ROWS:
            file_data['skip_rows'] = LogData(value=value, level=level)
        elif field == ExtractLoggerField.MSG:
            file_data['messages'].append(LogData(value=value, level=level))

    def log(self, scope, field, value, level=LogLevel.DEFAULT):
        assert scope in ExtractLoggerScope.ALL
        if scope == ExtractLoggerScope.GROUP:
            self._log_group_data(field=field, value=value, level=level)
        elif scope == ExtractLoggerScope.FILE:
            self._log_file_data(field=field, value=value, level=level)

    def print_header(self):
        grp_str = fit_string("Bill Group", self.GRP_WD)
        file_str = fit_string('Bill File', self.FILE_WD)
        rows_str = fit_string('Count', self.ROWS_WD, align=Align.RIGHT)
        msg_str = fit_string('Messages', self.MSG_WD)
        print(self.LINE_FORMAT.format(
            grp_str=f'{Color.HEADER}{grp_str}{Color.ENDC}',
            file_str=f'{Color.HEADER}{file_str}{Color.ENDC}',
            rows_str=f'{Color.HEADER}{rows_str}{Color.ENDC}',
            msg_str=f'{Color.HEADER}{msg_str}{Color.ENDC}',
        ))

    def print_line(self, account=None, file=None, rows=None, message=None):
        def _get_color_by_level(level, default=''):
            if level == LogLevel.ERROR:
                return Color.ERROR
            elif level == LogLevel.WARN:
                return Color.WARN
            return default

        if not self.header_printed:
            self.print_header()
            self.header_printed = True

        grp_str = ' ' * self.GRP_WD
        file_str = ' ' * self.FILE_WD
        rows_str = ' ' * self.ROWS_WD
        msg_str = ' ' * self.MSG_WD
        if account:
            color = _get_color_by_level(account.level, default=Color.OKCYAN)
            grp_str = fit_string(str(account.value), self.GRP_WD, placeholder_pos=-5)
            grp_str = f'{color}{grp_str}{Color.ENDC}'
        if file:
            color = _get_color_by_level(file.level, default=Color.OKCYAN)
            file_str = fit_string(str(file.value), self.FILE_WD, placeholder_pos=-9)
            file_str = f'{color}{file_str}{Color.ENDC}'
        if rows:
            color = _get_color_by_level(rows.level, default=Color.OKGREEN)
            rows_str = fit_string(str(rows.value), self.ROWS_WD, align=Align.RIGHT)
            rows_str = f'{color}{rows_str}{Color.ENDC}'
        if message:
            color = _get_color_by_level(message.level, default=Color.OKWHITE)
            msg_str = fit_string(str(message.value), self.MSG_WD)
            msg_str = f'{color}{msg_str}{Color.ENDC}'
        print(self.LINE_FORMAT.format(
            grp_str=grp_str,
            file_str=file_str,
            rows_str=rows_str,
            msg_str=msg_str,
        ))

    def print_group_data(self, group_data):
        g_line = 0
        for message in group_data['messages']:
            account = group_data['account'] if g_line == 0 else None
            self.print_line(account=account, message=message)
            g_line += 1

        for file_data in group_data['files']:
            f_line = 0
            for message in file_data['messages']:
                account = group_data['account'] if g_line == 0 else None
                file = file_data['file'] if f_line == 0 else None
                rows = file_data['rows'] if f_line == 0 else None
                self.print_line(account=account, file=file, rows=rows, message=message)
                f_line += 1
                g_line += 1
            if f_line == 0 and file_data['file']:
                account = group_data['account'] if g_line == 0 else None
                self.print_line(account=account, file=file_data['file'], rows=file_data['rows'])
                f_line += 1
                g_line += 1

        if g_line == 0 and group_data['account']:
            self.print_line(account=group_data['account'])
            g_line += 1

    def sync_log_level(self, group_data):
        """Set log level from the highest level log."""
        group_max = LogLevel.NONE
        if group_data['account']:
            group_max = max(group_data['account'].level, group_max)
        for message in group_data['messages']:
            group_max = max(message.level, group_max)

        for file_data in group_data['files']:
            file_max = LogLevel.NONE
            if file_data['file']:
                file_max = max(file_data['file'].level, file_max)
            if file_data['rows']:
                file_max = max(file_data['rows'].level, file_max)
            for message in file_data['messages']:
                file_max = max(message.level, file_max)

            file_data['file'].level = file_max
            group_max = max(file_max, group_max)

        group_data['account'].level = group_max
        return group_data

    def flush(self):
        """Clear and print all data.

        Always pop each data before printing to prevent infinite loop, since flush() will always
        be executed while any exception catched.
        """
        while self.data:
            group_data = self.data.pop(0)
            group_data = self.sync_log_level(group_data)
            self.print_group_data(group_data)

    def bill_file_ends(self):
        if len(self.data) == 0 or len(self.data[-1]['files']) == 0:
            return
        file_data = self.data[-1]['files'][-1]
        file_data['ended'] = True

    def bill_group_ends(self):
        if len(self.data) == 0:
            return
        group_data = self.data[-1]
        group_data['ended'] = True

        # flush
        self.flush()


extract_logger = ExtractLogger()


class LogContextManager:

    def __init__(self, scope, account=None, file=None):
        assert scope in ExtractLoggerScope.ALL
        if scope == ExtractLoggerScope.GROUP:
            assert account is not None
        elif scope == ExtractLoggerScope.FILE:
            assert file is not None

        self.scope = scope
        self.account = account
        self.file = file

    def __enter__(self):
        if self.scope == ExtractLoggerScope.GROUP:
            extract_logger.log(self.scope, ExtractLoggerField.ACCT, value=self.account)
        elif self.scope == ExtractLoggerScope.FILE:
            extract_logger.log(self.scope, ExtractLoggerField.FILE, value=self.file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None and not hasattr(exc_val, 'logged_by_bill_aggregator'):
            if isinstance(exc_val, BillAggBaseException):
                message = exc_val.message
            else:
                message = str(exc_val)
            message = message or 'Un-specified Error'

            extract_logger.log(self.scope, ExtractLoggerField.MSG,
                               value=message, level=LogLevel.ERROR)
            exc_val.logged_by_bill_aggregator = True

        if self.scope == ExtractLoggerScope.GROUP:
            extract_logger.bill_group_ends()
        elif self.scope == ExtractLoggerScope.FILE:
            extract_logger.bill_file_ends()

        suppress = False
        if exc_val is not None and isinstance(exc_val, BillAggException):
            suppress = True
        return suppress
