from abc import ABC, abstractmethod
import datetime

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

from bill_aggregator.consts import (
    AmountType,
    ACCT, DATE, TIME, NAME, MEMO, AMT, AMT_TYPE)
from bill_aggregator.exceptions import BillAggregatorException


FONT_SIZE = 11  # This global value may be changed
DEFAULT_TABLE_STYLE = 'Table Style Light 2'
LIGHT_GREEN = '#BFECC7'
DARK_GREEN = '#005600'
LIGHT_RED = '#FFC0C7'
DARK_RED = '#910007'

HEADER_ROWS = 1
MAX_ROW_IDX = 1048575


class BaseColumn(ABC):
    """Abstract base class for all types of columns"""

    def __init__(self, workbook, worksheet, col_idx, column_conf):
        self.workbook = workbook
        self.worksheet = worksheet
        self.col_idx = col_idx
        self.column_conf = column_conf

        self.width = None
        self.format_props = {}    # save format props for additional formats
        self.format = None

    def init_style(self):
        if 'style' not in self.column_conf:
            return

        style_conf = self.column_conf['style']
        if 'width' in style_conf:
            self.width = float(style_conf['width'])

        if 'align' in style_conf:
            self.format_props['align'] = style_conf['align']
        if 'number_format' in style_conf:
            self.format_props['num_format'] = style_conf['number_format']
        if 'wrap_text' in style_conf:
            self.format_props['text_wrap'] = style_conf['wrap_text']

        if self.format_props:
            self.format_props['font_size'] = FONT_SIZE    # font_size may be changed
            self.format = self.workbook.add_format(self.format_props)

        self.worksheet.set_column(
            self.col_idx, self.col_idx,
            width=self.width, cell_format=self.format,
        )

    @abstractmethod
    def write_cell(self, row_idx, row_data):
        pass

    def apply_conditional_format(self):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_conf = self.column_conf.get('style', {})
        self.inbound_bg_color = style_conf.get('inbound_bg_color', LIGHT_GREEN)
        self.inbound_font_color = style_conf.get('inbound_font_color', DARK_GREEN)

        self.inbound_format = None
        self.unknown_format = None

    def init_style(self):
        super().init_style()
        self.inbound_format = self.workbook.add_format(self.format_props)
        self.inbound_format.set_pattern(1)
        self.inbound_format.set_bg_color(self.inbound_bg_color)
        self.inbound_format.set_font_color(self.inbound_font_color)

    def write_cell(self, row_idx, row_data):
        self.worksheet.write_number(row_idx, self.col_idx, row_data[AMT])

    def apply_conditional_format(self):
        self.worksheet.conditional_format(
            HEADER_ROWS, self.col_idx, MAX_ROW_IDX, self.col_idx,
            options={
                'type':     'cell',
                'criteria': 'greater than',
                'value':     0,
                'format':    self.inbound_format,
            })


class AmountTypeColumn(BaseColumn):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inbound_value = self.column_conf['data']['inbound_value']
        self.outbound_value = self.column_conf['data']['outbound_value']
        self.unknown_value = self.column_conf['data']['unknown_value']
        style_conf = self.column_conf.get('style', {})
        self.unknown_bg_color = style_conf.get('unknown_bg_color', LIGHT_RED)
        self.unknown_font_color = style_conf.get('unknown_font_color', DARK_RED)

        self.unknown_format = None

    def init_style(self):
        super().init_style()
        self.unknown_format = self.workbook.add_format(self.format_props)
        self.unknown_format.set_pattern(1)
        self.unknown_format.set_bg_color(self.unknown_bg_color)
        self.unknown_format.set_font_color(self.unknown_font_color)

    def write_cell(self, row_idx, row_data):
        if row_data[AMT_TYPE] == AmountType.IN:
            self.worksheet.write_string(row_idx, self.col_idx, self.inbound_value)
        elif row_data[AMT_TYPE] == AmountType.OUT:
            self.worksheet.write_string(row_idx, self.col_idx, self.outbound_value)
        elif row_data[AMT_TYPE] == AmountType.UNKNOWN:
            self.worksheet.write_string(row_idx, self.col_idx, self.unknown_value)

    def apply_conditional_format(self):
        self.worksheet.conditional_format(
            HEADER_ROWS, self.col_idx, MAX_ROW_IDX, self.col_idx,
            options={
                'type':     'cell',
                'criteria': 'equal to',
                'value':    f'"{self.unknown_value}"',
                'format':   self.unknown_format,
            })



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
        nrows = len(self.data) + HEADER_ROWS
        ncols = len(self.export_conf['columns'])

        # create excel file
        file = self.workdir / f'{self.aggregation}.xlsx'
        self.workbook = xlsxwriter.Workbook(file)
        self.worksheet = self.workbook.add_worksheet(name=self.aggregation)

        # set default font size
        if 'font_size' in self.export_conf:
            global FONT_SIZE
            FONT_SIZE = self.export_conf['font_size']
            self.workbook.formats[0].set_font_size(FONT_SIZE)

        # set row height
        if 'row_height' in self.export_conf:
            row_height = self.export_conf['row_height']
            self.worksheet.set_default_row(height=row_height)

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
            column.init_style()

        # create table
        table_style = self.export_conf.get('table_style', DEFAULT_TABLE_STYLE)
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
            row_idx = i + HEADER_ROWS
            for column in self.columns:
                column.write_cell(row_idx, row_data)

    def apply_conditional_format(self):
        # first apply multi-column formats, so they will take precedence
        amount_column = None
        amount_type_column = None
        for column in self.columns:
            if isinstance(column, AmountColumn):
                amount_column = column
            elif isinstance(column, AmountTypeColumn):
                amount_type_column = column
        if (amount_column is not None) and (amount_type_column is None):
            raise BillAggregatorException(
                'You must export "amount_type" column if you export "amount" column, '
                'since amount_type is sometimes unknown.'
            )
        cell_string = xl_rowcol_to_cell(HEADER_ROWS, amount_type_column.col_idx)
        self.worksheet.conditional_format(
            HEADER_ROWS, amount_column.col_idx, MAX_ROW_IDX, amount_column.col_idx,
            options={
                'type':     'formula',
                'criteria': f'=${cell_string}="{amount_type_column.unknown_value}"',
                'format':   amount_type_column.unknown_format,
            })

        # then apply single-column formats
        for column in self.columns:
            column.apply_conditional_format()

    def save_workbook(self):
        self.workbook.close()

    def export_bills(self):
        self.init_workbook()
        self.write_data()
        self.apply_conditional_format()
        self.save_workbook()
