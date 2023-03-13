from bill_aggregator.consts import (
    LogLevel, ExtractLoggerScope, ExtractLoggerField, Color,
)
from bill_aggregator.exceptions import BillAggBaseException
from bill_aggregator.utils.string_util import Align, fit_string, wrap_string


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
        self.header_printed = False
        self.warn_count = 0
        self.error_count = 0

        self._reset_data()

    def _reset_data(self):
        self.data = []

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
        rows_str = fit_string('Items', self.ROWS_WD, align=Align.RIGHT)
        msg_str = 'Messages'
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

        msg_str_list = []
        grp_str, file_str, rows_str, msg_str = '', '', '', ''
        grp_color = Color.OKCYAN
        file_color = Color.OKCYAN
        rows_color = Color.OKGREEN
        msg_color = Color.OKWHITE
        if account:
            grp_str = str(account.value)
            grp_color = _get_color_by_level(account.level, default=grp_color)
        if file:
            file_str = str(file.value)
            file_color = _get_color_by_level(file.level, default=file_color)
        if rows:
            rows_str = str(rows.value)
            rows_color = _get_color_by_level(rows.level, default=rows_color)
        if message:
            msg_str_list = wrap_string(message.value, width=self.MSG_WD)
            msg_str = msg_str_list.pop(0)
            msg_color = _get_color_by_level(message.level, default=msg_color)
        grp_str = fit_string(grp_str, self.GRP_WD, placeholder_pos=-5)
        file_str = fit_string(file_str, self.FILE_WD, placeholder_pos=-9)
        rows_str = fit_string(rows_str, self.ROWS_WD, align=Align.RIGHT)
        print(self.LINE_FORMAT.format(
            grp_str=f'{grp_color}{grp_str}{Color.ENDC}',
            file_str=f'{file_color}{file_str}{Color.ENDC}',
            rows_str=f'{rows_color}{rows_str}{Color.ENDC}',
            msg_str=f'{msg_color}{msg_str}{Color.ENDC}',
        ))

        for msg_str in msg_str_list:
            print(self.LINE_FORMAT.format(
                grp_str=' ' * self.GRP_WD,
                file_str=' ' * self.FILE_WD,
                rows_str=' ' * self.ROWS_WD,
                msg_str=f'{msg_color}{msg_str}{Color.ENDC}',
            ))

    def print_group_data(self, group_data):
        g_line = 0

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

        f_line = 0
        for message in group_data['messages']:
            account = group_data['account'] if g_line == 0 else None
            file = LogData('N/A', level=group_data['account'].level) if f_line == 0 else None
            self.print_line(account=account, file=file, message=message)
            f_line += 1
            g_line += 1

        if g_line == 0 and group_data['account']:
            self.print_line(account=group_data['account'])
            g_line += 1

    def sync_log_level_and_update_count(self, group_data):
        """Set log level from the highest level log, update warning/error count."""
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

            if file_max == LogLevel.ERROR:
                self.error_count += 1
            elif file_max == LogLevel.WARN:
                self.warn_count += 1
            file_data['file'].level = file_max
            group_max = max(file_max, group_max)

        if group_data['messages'] or not group_data['files']:
            if group_max == LogLevel.ERROR:
                self.error_count += 1
            elif group_max == LogLevel.WARN:
                self.warn_count += 1
        group_data['account'].level = group_max
        return group_data

    def flush(self):
        """Print and clear all data."""
        for group_data in self.data:
            group_data = self.sync_log_level_and_update_count(group_data)
            self.print_group_data(group_data)

        self._reset_data()

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

    def complete(self):
        self.flush()
        message = 'Extracting completed.'

        warn_msg = f'{self.warn_count} warning{"" if self.warn_count == 1 else "s"}'
        error_msg = f'{self.error_count} error{"" if self.error_count == 1 else "s"}'
        warn_msg = f'{Color.WARN}{warn_msg}{Color.ENDC}'
        error_msg = f'{Color.ERROR}{error_msg}{Color.ENDC}'
        if self.warn_count and self.error_count:
            message += f' ({warn_msg}, {error_msg})'
        elif self.warn_count:
            message += f' ({warn_msg})'
        elif self.error_count:
            message += f' ({error_msg})'
        print(message)


extract_logger = ExtractLogger()


class ExtractLoggerContextManager:

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
                message = f'{exc_type.__name__}: {str(exc_val)}'

            extract_logger.log(self.scope, ExtractLoggerField.MSG,
                               value=message, level=LogLevel.ERROR)
            exc_val.logged_by_bill_aggregator = True

        if self.scope == ExtractLoggerScope.GROUP:
            extract_logger.bill_group_ends()
        elif self.scope == ExtractLoggerScope.FILE:
            extract_logger.bill_file_ends()

        suppress = False
        if exc_val is not None and isinstance(exc_val, BillAggBaseException):
            suppress = True
        return suppress
