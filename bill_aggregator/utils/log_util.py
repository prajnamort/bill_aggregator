from functools import wraps

from bill_aggregator.consts import LogLevel, ExtractLoggerScope, ExtractLoggerField


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

    def __init__(self):
        self._clear_data()

    def _clear_data(self):
        self.data = []

    def _new_group_data(self):
        return {
            'account': None,
            'messages': [],
            'files': [],
            'ended': False,
        }

    def _new_file_data(self):
        return {
            'file': None,
            'rows': None,
            'skip_rows': None,
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

    def _log_group_data(self, field, value):
        assert field in ExtractLoggerField.GROUP_ALL

        group_data = self._last_or_new_group_data()
        if field == ExtractLoggerField.ACCT:
            group_data['account'] = value
        elif field == ExtractLoggerField.MSG:
            group_data['messages'].append(value)

    def _log_file_data(self, field, value):
        assert field in ExtractLoggerField.FILE_ALL

        file_data = self._last_or_new_file_data()
        if field == ExtractLoggerField.FILE:
            file_data['file'] = value
        elif field == ExtractLoggerField.ROWS:
            file_data['rows'] = int(value)
        elif field == ExtractLoggerField.SKIP_ROWS:
            file_data['skip_rows'] = int(value)
        elif field == ExtractLoggerField.MSG:
            file_data['messages'].append(value)

    def log(self, scope, field, value, level=LogLevel.INFO):
        assert scope in ExtractLoggerScope.ALL
        assert level in LogLevel.ALL

        if scope == ExtractLoggerScope.GROUP:
            self._log_group_data(field=field, value=value)
        elif scope == ExtractLoggerScope.FILE:
            self._log_file_data(field=field, value=value)

    def flush(self):
        # print data
        print(self.data)

        # clear data
        self._clear_data()

    def bill_file_ends(self):
        file_data = self._last_or_new_file_data()
        file_data['ended'] = True

    def bill_group_ends(self):
        group_data = self._last_or_new_group_data()
        group_data['ended'] = True
        self.flush()


extract_logger = ExtractLogger()


def with_extract_logger(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper
