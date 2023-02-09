import csv

from charset_normalizer import from_path

from bill_aggregator import consts
from bill_aggregator import exceptions


class CsvExtractor:

    def __init__(self, file, file_conf):
        self.file = file
        self.file_conf = file_conf

        self.rows = []
        self.column_count = 0
        self.has_header = self.file_conf['has_header']
        self.header_row = []
        self.data_rows = []

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
        if column_count < consts.MIN_BILL_COLUMNS:
            self.rows = []
            return

        self.column_count = column_count
        self.rows = [row for row in self.rows if len(row) == self.column_count]

        new_row_count = len(self.rows)
        diff_row_count = orig_row_count - new_row_count
        if diff_row_count >= consts.WARN_TRIM_ROW_COUNT:
            print(f'Trimed {diff_row_count} rows.')

    def seperate_header_and_data_rows(self):
        """Seperate header_row and data_rows, if header exists."""
        if not self.has_header:
            return
        if not self.rows:
            raise exceptions.BillAggregatorException('No valid rows')
        self.header_row = self.rows[0]
        self.data_rows = self.rows[1:]

    def extract_bills(self):
        print(f'Handling file: {self.file.name}')

        self.read_csv_file()
        self.update_column_count_and_trim_rows()
        self.seperate_header_and_data_rows()

        print(len(self.rows))
        print(self.has_header)
