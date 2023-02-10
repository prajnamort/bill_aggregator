import csv
import pandas

from charset_normalizer import from_path

from bill_aggregator.consts import (
    MIN_BILL_COLUMNS, WARN_TRIM_ROW_COUNT, AmountFormat, RC,
)
from bill_aggregator import exceptions


class CsvExtractor:

    def __init__(self, file, file_conf):
        self.file = file
        self.file_conf = file_conf

        self.rows = []
        self.column_count = 0
        self.has_header = self.file_conf['has_header']
        self.header_row = None
        self.data_rows = None
        self.data = None

    def read_csv_file(self):
        """Read original csv file into self.rows"""
        encoding = self.file_conf.get('encoding')
        if not encoding:
            result = from_path(self.file).best()
            if not result:
                raise exceptions.BillAggregatorException('Cannot detect encoding')
            print(f'Detected encoding: {result.encoding}, confidence: {1.0 - result.chaos}')
            encoding = result.encoding

        with open(self.file, 'r', encoding=encoding) as f:
            csvreader = csv.reader(f)
            self.rows = list(csvreader)

    def update_column_count_and_trim_rows(self):
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

    def strip_all_fields(self):
        """Trim all fields, in both header and data rows."""
        results = []
        for row in self.rows:
            results.append([f.strip() for f in row])
        self.rows = results

    def seperate_header_and_data_rows(self):
        """Seperate header_row and data_rows, if header exists."""
        if self.has_header:
            if not self.rows:
                raise exceptions.BillAggregatorException('No valid rows')
            self.header_row = self.rows[0]
            self.data_rows = self.rows[1:]
        else:
            self.data_rows = self.rows

    def check_config_against_data(self):
        ## Gather the columns which will be used
        check_columns = []
        # required columns
        check_columns.append(self.file_conf['fields']['date']['column'])
        check_columns.append(self.file_conf['fields']['name']['column'])
        # optional columns
        if 'memo' in self.file_conf['fields']:
            check_columns.append(self.file_conf['fields']['memo']['column'])
        # amount columns
        amount_conf = self.file_conf['fields']['amount']
        if amount_conf['format'] == AmountFormat.ONE_COLUMN_WITH_INDICATORS:
            check_columns.append(amount_conf['column'])
            for idc_c in amount_conf['indicators']:
                check_columns.append(idc_c['column'])
        elif amount_conf['format'] == AmountFormat.ONE_COLUMN_WITH_SIGN:
            check_columns.append(amount_conf['column'])
        # extra columns
        if 'extra_fields' in self.file_conf:
            check_columns.extend(fc['column'] for fc in self.file_conf['extra_fields'].values())

        ## Check if these columns actually exists
        for col in check_columns:
            if isinstance(col, int):
                if col >= self.column_count:
                    raise exceptions.BillAggregatorException(f'No such column: {col}')
            elif isinstance(col, str):
                match_column_count = self.header_row.count(col)
                if match_column_count == 0:
                    raise exceptions.BillAggregatorException(f'No such column: {col}')
                elif match_column_count >= 2:
                    raise exceptions.BillAggregatorException(f'Multiple Column exists: {col}')
            else:
                raise exceptions.BillAggregatorException('Unrecognized column indicator')

    def prepare_data(self):
        self.read_csv_file()
        self.update_column_count_and_trim_rows()
        self.strip_all_fields()
        self.seperate_header_and_data_rows()
        self.check_config_against_data()

        self.data = pandas.DataFrame(
            data=self.data_rows,
            columns=self.header_row)
        self.data[RC] = [{} for _ in range(len(self.data))]

    def process_date_field(self):
        date_conf = self.file_conf['fields']['date']
        date_col = date_conf['column']

        kwargs = {}
        if 'dayfirst' in date_conf:
            kwargs['dayfirst'] = date_conf['dayfirst']

        self.data[date_col] = pandas.to_datetime(self.data[date_col], **kwargs)

    def process_data(self):
        self.process_date_field()

    def extract_bills(self):
        print(f'Handling file: {self.file.name}')

        self.prepare_data()
        self.process_data()

        print(len(self.data_rows))
        print(self.data.size)
