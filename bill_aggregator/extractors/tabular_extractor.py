import csv
from io import StringIO
from abc import abstractmethod
from functools import partial

import xlrd
import dateutil.parser
import charset_normalizer

from bill_aggregator.consts import (
    MIN_BILL_COLUMNS, AmountFormat, AmountType,
    FIELDS, EXT_FIELDS, COL, FORMAT, DATE, TIME, NAME, MEMO, AMT, AMT_TYPE,
    ExtractLoggerScope, ExtractLoggerField,
)
from bill_aggregator.exceptions import BillAggException
from bill_aggregator.utils import amount_util
from bill_aggregator.utils.log_util import extract_logger
from .base_extractor import BaseExtractor


RES_COL = -1    # Column for storing temporary results


class TabularExtractor(BaseExtractor):
    """Abstract base class for tabular file types (e.g. csv, xls...)"""

    def __init__(self, file, file_conf):
        super().__init__(file=file, file_conf=file_conf)
        self.has_header = self.file_conf['has_header']

        self.column_count = 0
        self.header_row = None
        self.rows = []

    @abstractmethod
    def load_file(self):
        """Read data from tabular file into self.rows"""
        pass

    def _seperate_header_row(self):
        """Seperate header and data rows, if header exists."""
        if not self.has_header:
            return
        if not self.rows:
            raise BillAggException('Cannot find header: no valid rows')
        self.header_row = self.rows[0]
        self.rows = self.rows[1:]

    def _strip_all_fields(self):
        """Trim all fields, in both header and data rows."""
        if self.header_row:
            self.header_row = [f.strip() for f in self.header_row]

        results = []
        for row in self.rows:
            results.append([f.strip() for f in row])
        self.rows = results

    def _check_column(self, col):
        """Check if column exist, return column number as integer."""
        if isinstance(col, int):
            if col >= self.column_count:
                raise BillAggException(f'Config Error, no such column: {col}, ' \
                                       f'available columns: 0-{self.column_count-1}')
            return col
        elif isinstance(col, str):
            match_column_count = self.header_row.count(col)
            if match_column_count == 0:
                raise BillAggException(f'Config Error, no such column: "{col}", ' \
                                       f'available columns: {self.header_row}')
            elif match_column_count >= 2:
                raise BillAggException(f'Multiple Column "{col}" exists')
            return self.header_row.index(col)
        elif isinstance(col, list):
            return [self._check_column(c) for c in col]
        raise BillAggException(f'Config Error, unrecognized column indicator: {col}')

    def _check_and_update_config(self):
        """Check config against the actual data, update config if needed."""
        # required columns
        self.file_conf[FIELDS][DATE][COL] = self._check_column(
            self.file_conf[FIELDS][DATE][COL])
        self.file_conf[FIELDS][NAME][COL] = self._check_column(
            self.file_conf[FIELDS][NAME][COL])
        # optional columns
        if TIME in self.file_conf[FIELDS]:
            self.file_conf[FIELDS][TIME][COL] = self._check_column(
                self.file_conf[FIELDS][TIME][COL])
        if MEMO in self.file_conf[FIELDS]:
            self.file_conf[FIELDS][MEMO][COL] = self._check_column(
                self.file_conf[FIELDS][MEMO][COL])
        # amount columns
        amount_c = self.file_conf[FIELDS][AMT]
        if amount_c[FORMAT] == AmountFormat.ONE_COLUMN_WITH_INDICATORS:
            amount_c[COL] = self._check_column(amount_c[COL])
            for indicator_c in amount_c['indicators']:
                indicator_c[COL] = self._check_column(indicator_c[COL])
        elif amount_c[FORMAT] == AmountFormat.ONE_COLUMN_WITH_SIGN:
            amount_c[COL] = self._check_column(amount_c[COL])
        elif amount_c[FORMAT] == AmountFormat.TWO_COLUMNS:
            amount_c['inbound'][COL] = self._check_column(amount_c['inbound'][COL])
            amount_c['outbound'][COL] = self._check_column(amount_c['outbound'][COL])
        # extra columns
        if EXT_FIELDS in self.file_conf:
            for field_c in self.file_conf[EXT_FIELDS].values():
                field_c[COL] = self._check_column(field_c[COL])

    def _process_date_time_fields(self):
        date_conf = self.file_conf[FIELDS][DATE]
        date_cols = date_conf[COL]
        time_col = None
        if TIME in self.file_conf[FIELDS]:
            time_col = self.file_conf[FIELDS][TIME][COL]

        dayfirst = None
        yearfirst = None
        if 'dayfirst' in date_conf:
            dayfirst = date_conf['dayfirst']
        if 'yearfirst' in date_conf:
            yearfirst = date_conf['yearfirst']

        for row in self.rows:
            if isinstance(date_cols, list):
                date_col = next((col for col in date_cols if row[col]), None)
                if date_col is None:
                    raise BillAggException(f'No valid date for row: {row}')
            else:
                date_col = date_cols

            if time_col is None:
                dt_str = f'{row[date_col]}'
            else:
                dt_str = f'{row[date_col]} {row[time_col]}'
            dt = dateutil.parser.parse(dt_str, dayfirst=dayfirst, yearfirst=yearfirst)
            row[RES_COL][DATE] = dt.date()
            row[RES_COL][TIME] = dt.time()

    def _sort_data_by_datetime(self):
        def _sort_key(row):
            return (row[RES_COL][DATE], row[RES_COL][TIME])

        if _sort_key(self.rows[0]) > _sort_key(self.rows[-1]):
            self.rows.reverse()
        if not all(_sort_key(self.rows[i]) <= _sort_key(self.rows[i+1])
                   for i in range(len(self.rows) - 1)):
            self.rows.sort(key=_sort_key)    # stable sort (if same key, order is preserved)
            # logging
            extract_logger.log(
                ExtractLoggerScope.FILE, ExtractLoggerField.MSG,
                value='Re-sorted by transaction date')

    def _process_name_field(self):
        name_col = self.file_conf[FIELDS][NAME][COL]
        for row in self.rows:
            row[RES_COL][NAME] = row[name_col]

    def _process_memo_field(self):
        if MEMO in self.file_conf[FIELDS]:
            memo_col = self.file_conf[FIELDS][MEMO][COL]
            for row in self.rows:
                row[RES_COL][MEMO] = row[memo_col]
        else:
            for row in self.rows:
                row[RES_COL][MEMO] = ''

    def _process_one_col_with_idcs_amt_fields(self):
        amt_conf = self.file_conf[FIELDS][AMT]
        amt_col = amt_conf[COL]
        idc_confs = amt_conf['indicators']

        for row in self.rows:
            amount = amount_util.convert_amount_to_decimal(row[amt_col])
            amount_type = AmountType.UNKNOWN
            for idc_conf in idc_confs:
                idc_col = idc_conf[COL]
                if row[idc_col] == idc_conf['inbound_value']:
                    amount_type = AmountType.IN
                    break
                elif row[idc_col] == idc_conf['outbound_value']:
                    amount_type = AmountType.OUT
                    break

            if amount_type == AmountType.IN:
                amount = amount.copy_sign(amount_util.POS)
            elif amount_type == AmountType.OUT:
                amount = amount.copy_sign(amount_util.NEG)
            row[RES_COL][AMT] = amount
            row[RES_COL][AMT_TYPE] = amount_type

    def _process_one_col_with_sign_amt_fields(self):
        amt_conf = self.file_conf[FIELDS][AMT]
        amt_col = amt_conf[COL]

        reverse_sign = False
        if 'is_outbound_positive' in amt_conf:
            reverse_sign = amt_conf['is_outbound_positive']

        for row in self.rows:
            amount = amount_util.convert_amount_to_decimal(row[amt_col])
            if bool(amount.is_signed()) ^ bool(reverse_sign):
                amount_type = AmountType.OUT
                amount = amount.copy_sign(amount_util.NEG)
            else:
                amount_type = AmountType.IN
                amount = amount.copy_sign(amount_util.POS)
            row[RES_COL][AMT] = amount
            row[RES_COL][AMT_TYPE] = amount_type

    def _process_two_cols_amt_fields(self):
        amt_conf = self.file_conf[FIELDS][AMT]
        amt_in_col = amt_conf['inbound'][COL]
        amt_out_col = amt_conf['outbound'][COL]

        for row in self.rows:
            amount_in = amount_util.POS_ZERO
            amount_out = amount_util.NEG_ZERO
            if row[amt_in_col]:
                amount_in = amount_util.convert_amount_to_decimal(row[amt_in_col])
                amount_in = amount_in.copy_sign(amount_util.POS)
            if row[amt_out_col]:
                amount_out = amount_util.convert_amount_to_decimal(row[amt_out_col])
                amount_out = amount_out.copy_sign(amount_util.NEG)

            amount = amount_in + amount_out
            if amount.is_signed():
                amount_type = AmountType.OUT
            else:
                amount_type = AmountType.IN
            if amount == 0 and row[amt_out_col]:
                # if outbound field exist, treat 0 as OUT (0 default to IN)
                amount_type = AmountType.OUT
                amount = amount.copy_sign(amount_util.NEG)
            row[RES_COL][AMT] = amount
            row[RES_COL][AMT_TYPE] = amount_type

    def _process_amount_fields(self):
        amt_format = self.file_conf[FIELDS][AMT][FORMAT]
        if amt_format == AmountFormat.ONE_COLUMN_WITH_INDICATORS:
            self._process_one_col_with_idcs_amt_fields()
        elif amt_format == AmountFormat.ONE_COLUMN_WITH_SIGN:
            self._process_one_col_with_sign_amt_fields()
        elif amt_format == AmountFormat.TWO_COLUMNS:
            self._process_two_cols_amt_fields()
        else:
            raise BillAggException(f'Config Error, invalid amount format: {amt_format}')

    def _process_extra_fields(self):
        if EXT_FIELDS not in self.file_conf:
            return
        for row in self.rows:
            for field_name, field_conf in self.file_conf[EXT_FIELDS].items():
                field_value = row[field_conf[COL]]
                row[RES_COL][field_name] = field_value

    def prepare_data(self):
        """Get the data in self.rows prepared for further processing"""
        self._seperate_header_row()
        self._strip_all_fields()
        self._check_and_update_config()

        for row in self.rows:
            row.append({})    # append result column

    def process_data(self):
        """Process data in self.rows, then put them in self.results"""
        self._process_date_time_fields()
        self._sort_data_by_datetime()
        self._process_name_field()
        self._process_memo_field()
        self._process_amount_fields()
        self._process_extra_fields()

        for row in self.rows:
            self.results.append(row[RES_COL])

    def extract_bills(self):
        """Main entry point for Extractor"""
        self.load_file()
        self.prepare_data()
        self.process_data()


class CsvExtractor(TabularExtractor):

    def __init__(self, file, file_conf):
        super().__init__(file=file, file_conf=file_conf)
        self.encoding = self.file_conf.get('encoding', None)
        self.delimiter = self.file_conf.get('delimiter', ',')

    def _read_csv_file(self):
        """Read original csv file into self.rows"""
        if self.encoding:
            file_func = partial(open, self.file, 'r', encoding=self.encoding)
        else:
            result = charset_normalizer.from_path(self.file).best()
            if not result:
                raise BillAggException('Cannot detect encoding')

            # logging
            msg = f'Detected encoding: {result.encoding} (confidence: {1.0 - result.chaos:.2})'
            extract_logger.log(ExtractLoggerScope.FILE, ExtractLoggerField.MSG, value=msg)

            file_func = partial(StringIO, str(result))

        with file_func() as f:
            csvreader = csv.reader(f, delimiter=self.delimiter)
            self.rows = list(csvreader)

    def _update_column_count_and_trim_rows(self):
        """Update column_count, and trim rows"""
        orig_row_count = len(self.rows)
        if not orig_row_count:
            return

        column_count = max(len(row) for row in self.rows)
        if column_count < MIN_BILL_COLUMNS:
            self.rows = []
            return

        self.column_count = column_count
        self.rows = [row for row in self.rows if len(row) == self.column_count]

        # logging
        new_row_count = len(self.rows)
        diff_row_count = orig_row_count - new_row_count
        extract_logger.log(
            ExtractLoggerScope.FILE, ExtractLoggerField.SKIP_ROWS, value=diff_row_count)

    def load_file(self):
        self._read_csv_file()
        self._update_column_count_and_trim_rows()


class XlsExtractor(TabularExtractor):

    def __init__(self, file, file_conf):
        super().__init__(file=file, file_conf=file_conf)
        self.skiprows = self.file_conf.get('skiprows', 0)
        self.skipfooters = self.file_conf.get('skipfooters', 0)

    def load_file(self):
        """Read original csv file into self.rows"""
        sheet = xlrd.open_workbook(self.file).sheet_by_index(0)
        start = 0 + self.skiprows
        end = (sheet.nrows - 1) - self.skipfooters
        total_skiprows = self.skiprows + self.skipfooters

        if start > end:
            raise BillAggException(f'Config Error, need to skip {total_skiprows} rows, ' \
                                   f'only {sheet.nrows} rows found')

        results = []
        for i in range(start, end+1):
            row = [str(cell.value) for cell in sheet.row(i)]
            results.append(row)
        self.rows = results
        self.column_count = len(self.rows[0])

        # logging
        extract_logger.log(
            ExtractLoggerScope.FILE, ExtractLoggerField.SKIP_ROWS, value=total_skiprows)
