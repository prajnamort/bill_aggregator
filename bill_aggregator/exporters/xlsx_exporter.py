from abc import ABC, abstractmethod
import datetime

import xlsxwriter

from bill_aggregator.consts import (
    AmountType,
    ACCT, DATE, TIME, NAME, MEMO, AMT, AMT_TYPE)
from bill_aggregator.exceptions import BillAggregatorException


FONT_SIZE = 11


class BaseColumn(ABC):
    """Abstract base class for all types of columns"""

    def __init__(self, workbook, worksheet, col_idx, column_conf):
        self.workbook = workbook
        self.worksheet = worksheet
        self.col_idx = col_idx
        self.column_conf = column_conf

        self.width = None
        self.format = None

    def set_column_style(self):
        if 'style' not in self.column_conf:
            return

        style_conf = self.column_conf['style']
        if 'width' in style_conf:
            self.width = float(style_conf['width'])

        format_props = {}
        if 'align' in style_conf:
            format_props['align'] = style_conf['align']
        if 'number_format' in style_conf:
            format_props['num_format'] = style_conf['number_format']
        if format_props:
            format_props['font_size'] = FONT_SIZE
            self.format = self.workbook.add_format(format_props)

        self.worksheet.set_column(
            self.col_idx, self.col_idx,
            width=self.width, cell_format=self.format,
        )

    @abstractmethod
    def write_cell(self, row_idx, row_data):
        pass


class DateColumn(BaseColumn):

    def write_cell(self, row_idx, row_data):
        self.worksheet.write_datetime(row_idx, self.col_idx, row_data[DATE])


class TimeColumn(BaseColumn):

    def write_cell(self, row_idx, row_data):
        if row_data[TIME] == datetime.time(0):
            return
        self.worksheet.write_datetime(row_idx, self.col_idx, row_data[TIME])


class AccountColumn(BaseColumn):

    def write_cell(self, row_idx, row_data):
        self.worksheet.write_string(row_idx, self.col_idx, row_data[ACCT])


class NameColumn(BaseColumn):

    def write_cell(self, row_idx, row_data):
        self.worksheet.write_string(row_idx, self.col_idx, row_data[NAME])


class MemoColumn(BaseColumn):

    def write_cell(self, row_idx, row_data):
        self.worksheet.write_string(row_idx, self.col_idx, row_data[MEMO])


class AmountColumn(BaseColumn):

    def write_cell(self, row_idx, row_data):
        self.worksheet.write_number(row_idx, self.col_idx, row_data[AMT])


class AmountTypeColumn(BaseColumn):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inbound_value = self.column_conf['data']['inbound_value']
        self.outbound_value = self.column_conf['data']['outbound_value']
        self.unknown_value = self.column_conf['data']['unknown_value']

    def write_cell(self, row_idx, row_data):
        if row_data[AMT_TYPE] == AmountType.IN:
            self.worksheet.write_string(row_idx, self.col_idx, self.inbound_value)
        elif row_data[AMT_TYPE] == AmountType.OUT:
            self.worksheet.write_string(row_idx, self.col_idx, self.outbound_value)
        elif row_data[AMT_TYPE] == AmountType.UNKNOWN:
            self.worksheet.write_string(row_idx, self.col_idx, self.unknown_value)


class EmptyColumn(BaseColumn):

    def write_cell(self, row_idx, row_data):
        pass


class CustomColumn(BaseColumn):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = self.column_conf['data']['value']

    def write_cell(self, row_idx, row_data):
        self.worksheet.write_string(row_idx, self.col_idx, self.value)


field_to_column_map = {
    DATE: DateColumn,
    TIME: TimeColumn,
    ACCT: AccountColumn,
    NAME: NameColumn,
    MEMO: MemoColumn,
    AMT: AmountColumn,
    AMT_TYPE: AmountTypeColumn,
}


class XlsxExporter:

    def __init__(self, data, aggregation, export_conf, workdir):
        self.data = data
        self.aggregation = aggregation
        self.export_conf = export_conf
        self.workdir = workdir

        self.workbook = None
        self.worksheet = None
        self.columns = []

    def _get_column_cls(self, column_conf):
        data_conf = column_conf['data']
        data_type = data_conf['type']
        if data_type == 'data':
            return field_to_column_map[data_conf['field']]
        elif data_type == 'empty':
            return EmptyColumn
        elif data_type == 'custom':
            return CustomColumn
        else:
            raise BillAggregatorException(f'Invalid data type: {data_type}')

    def init_workbook(self):
        # create excel file
        file = self.workdir / f'{self.aggregation}.xlsx'
        self.workbook = xlsxwriter.Workbook(file)
        self.worksheet = self.workbook.add_worksheet(name=self.aggregation)

        # set default font size
        if 'font_size' in self.export_conf:
            global FONT_SIZE
            FONT_SIZE = self.export_conf['font_size']
            self.workbook.formats[0].set_font_size(FONT_SIZE)

        # create all column instances
        self.columns = []
        for col_idx, column_conf in enumerate(self.export_conf['columns']):
            ColumnCls = self._get_column_cls(column_conf)
            column = ColumnCls(
                workbook=self.workbook, worksheet=self.worksheet,
                col_idx=col_idx, column_conf=column_conf)
            self.columns.append(column)
        # set all column styles
        for column in self.columns:
            column.set_column_style()

        # create table
        nrows = len(self.data) + 1    # additional 1 for header row
        ncols = len(self.export_conf['columns'])
        table_style = self.export_conf.get('table_style', 'Table Style Light 2')
        self.worksheet.add_table(
            0, 0,
            nrows-1, ncols-1,
            options={
                'header_row': True,
                'style': table_style,
                'columns': [{'header': cc['header']} for cc in self.export_conf['columns']],
            })

    def write_data(self):
        for i, row_data in enumerate(self.data):
            row_idx = i + 1    # additional 1 for header row
            for column in self.columns:
                column.write_cell(row_idx, row_data)

    def save_workbook(self):
        self.workbook.close()

    def export_bills(self):
        self.init_workbook()
        self.write_data()
        self.save_workbook()
