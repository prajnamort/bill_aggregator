import csv
import dateparser

from charset_normalizer import from_path

from bill_aggregator.consts import (
    MIN_BILL_COLUMNS, WARN_TRIM_ROW_COUNT, AmountFormat, AmountType,
    FIELDS, EXT_FIELDS, COL, FORMAT, DATE, TIME, NAME, MEMO, AMT, AMT_TYPE
)
from bill_aggregator.exceptions import BillAggregatorException
from bill_aggregator.utils import amount_util


RES_COL = -1    # Column for storing temporary results


class CsvExtractor:

    def __init__(self, file, file_conf):
        self.file = file
        self.file_conf = file_conf

        self.rows = []
        self.column_count = 0
        self.has_header = self.file_conf['has_header']
        self.header_row = None

    def _read_csv_file(self):
        """Read original csv file into self.rows"""
        encoding = self.file_conf.get('encoding')
        if not encoding:
            result = from_path(self.file).best()
            if not result:
                raise BillAggregatorException('Cannot detect encoding')
            print(f'Detected encoding: {result.encoding}, confidence: {1.0 - result.chaos}')
            encoding = result.encoding

        with open(self.file, 'r', encoding=encoding) as f:
            csvreader = csv.reader(f)
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

        new_row_count = len(self.rows)
        diff_row_count = orig_row_count - new_row_count
        if diff_row_count >= WARN_TRIM_ROW_COUNT:
            print(f'Trimed {diff_row_count} rows.')

    def _strip_all_fields(self):
        """Trim all fields, in both header and data rows."""
        results = []
        for row in self.rows:
            results.append([f.strip() for f in row])
        self.rows = results

    def _seperate_header_row(self):
        """Seperate header and data rows, if header exists."""
        if not self.has_header:
            return

        if not self.rows:
            raise BillAggregatorException('No valid rows')
        self.header_row = self.rows[0]
        self.rows = self.rows[1:]

    def _check_column(self, col):
        """Check if column exist, return column number as integer."""
        if isinstance(col, int):
            if col >= self.column_count:
                raise BillAggregatorException(f'No such column: {col}')
            return col
        elif isinstance(col, str):
            match_column_count = self.header_row.count(col)
            if match_column_count == 0:
                raise BillAggregatorException(f'No such column: {col}')
            elif match_column_count >= 2:
                raise BillAggregatorException(f'Multiple Column exists: {col}')
            return self.header_row.index(col)
        raise BillAggregatorException('Unrecognized column indicator')

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
        if amount_c['format'] == AmountFormat.ONE_COLUMN_WITH_INDICATORS:
            amount_c[COL] = self._check_column(amount_c[COL])
            for indicator_c in amount_c['indicators']:
                indicator_c[COL] = self._check_column(indicator_c[COL])
        elif amount_c['format'] == AmountFormat.ONE_COLUMN_WITH_SIGN:
            amount_c[COL] = self._check_column(amount_c[COL])
        # extra columns
        if EXT_FIELDS in self.file_conf:
            for field_c in self.file_conf[EXT_FIELDS].values():
                field_c[COL] = self._check_column(field_c[COL])

    def prepare_data(self):
        """Read data from csv file, and get them prepared in self.rows"""
        self._read_csv_file()
        self._update_column_count_and_trim_rows()
        self._strip_all_fields()
        self._seperate_header_row()
        self._check_and_update_config()

        for row in self.rows:
            row.append({})    # append result column

    def _process_date_time_fields(self):
        date_conf = self.file_conf[FIELDS][DATE]
        date_col = date_conf[COL]
        time_col = None
        parser_settings = {}
        if TIME in self.file_conf[FIELDS]:
            time_col = self.file_conf[FIELDS][TIME][COL]
        if 'date_order' in date_conf:
            parser_settings['DATE_ORDER'] = date_conf['date_order']

        for row in self.rows:
            if time_col is None:
                dt_str = f'{row[date_col]}'
            else:
                dt_str = f'{row[date_col]} {row[time_col]}'
            dt = dateparser.parse(dt_str, settings=parser_settings)
            if dt is None:
                raise BillAggregatorException(f'Cannot parse date: {row[date_col]}')
            row[RES_COL][DATE] = dt.date()
            row[RES_COL][TIME] = dt.time()

    def _sort_data_by_datetime(self):
        def _key(row):
            return (row[RES_COL][DATE], row[RES_COL][TIME])

        if _key(self.rows[0]) > _key(self.rows[-1]):
            self.rows.reverse()
        if not all(_key(self.rows[i]) <= _key(self.rows[i+1]) for i in range(len(self.rows) - 1)):
            print('Sort performed')
            self.rows.sort(key=_key)

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
                amount.copy_sign(amount_util.POS)
            elif amount_type == AmountType.OUT:
                amount.copy_sign(amount_util.NEG)
            row[RES_COL][AMT] = amount
            row[RES_COL][AMT_TYPE] = amount_type

    def _process_one_col_with_sign_amt_fields(self):
        amt_conf = self.file_conf[FIELDS][AMT]
        amt_col = amt_conf[COL]

        for row in self.rows:
            amount = amount_util.convert_amount_to_decimal(row[amt_col])
            if amount.is_signed():
                amount_type = AmountType.OUT
            else:
                amount_type = AmountType.IN
            row[RES_COL][AMT] = amount
            row[RES_COL][AMT_TYPE] = amount_type

    def _process_amount_fields(self):
        amt_format = self.file_conf[FIELDS][AMT][FORMAT]
        if amt_format == AmountFormat.ONE_COLUMN_WITH_INDICATORS:
            self._process_one_col_with_idcs_amt_fields()
        elif amt_format == AmountFormat.ONE_COLUMN_WITH_SIGN:
            self._process_one_col_with_sign_amt_fields()
        else:
            raise BillAggregatorException(f'invalid amount format: {amt_format}')

    def _process_extra_fields(self):
        if EXT_FIELDS not in self.file_conf:
            return
        for row in self.rows:
            for field_name, field_conf in self.file_conf[EXT_FIELDS].items():
                field_value = row[field_conf[COL]]
                row[RES_COL][field_name] = field_value

    def process_data(self):
        """Start processing data in self.rows"""
        self._process_date_time_fields()
        self._sort_data_by_datetime()
        self._process_name_field()
        self._process_memo_field()
        self._process_amount_fields()
        self._process_extra_fields()

    def extract_bills(self):
        """Main entry point for this Extractor"""
        print(f'Handling file: {self.file.name}')

        self.prepare_data()
        self.process_data()

        print(len(self.rows))
        for row in self.rows:
            print(row[RES_COL])
