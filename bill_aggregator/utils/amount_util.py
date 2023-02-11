import re
from decimal import Decimal

from bill_aggregator.exceptions import BillAggregatorException


REAL_DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
DECIMAL_SEPS = ['.', ',']
DEFAULT_DECIMAL_SEP = '.'

POS = Decimal('1')
NEG = Decimal('-1')


def convert_amount_to_decimal(amount, decimal_separator=None):
    """Convert currency amount from string to decimal.

    Input:
        '-$6,150,593.22'
        '￥6,150,593.22-'
        '(HK$6,150,593.22)'
        '-Eu6.150.593,22'
        '-6.150.593,22 R$'
        'Sk 6 150 593,22-'
        '-6 150 593,22 грн.'
        'z³ 6 150 593,22-'
    All inputs above should return:
        Decimal('-6150593.22')
    """
    assert isinstance(amount, str)

    # extract negative sign, turn into absolute value
    negative = False
    if '-' in amount or '(' in amount:
        negative = True
        amount = re.sub(r'[-()]', '', amount)

    # strip currency symbol
    amount = list(amount)
    for c in amount.copy():
        if c in REAL_DIGITS:
            break
        amount.pop(0)
    for c in reversed(amount.copy()):
        if c in REAL_DIGITS:
            break
        amount.pop()
    amount = ''.join(amount)

    # detect decimal_separator
    if decimal_separator is None:
        decimal_separator = detect_decimal_separator(amount)

    # remove anything other than digits and decimal_separator
    result = []
    for c in amount:
        if c in REAL_DIGITS:
            result.append(c)
        if decimal_separator is not None and c == decimal_separator:
            result.append('.')
    result = ''.join(result)

    # add the negative sign if needed
    if negative:
        result = '-' + result

    return Decimal(result)


def detect_decimal_separator(amount):
    """Detect decimal separator for a financial amount.

    Assumes that any financial amount should have at most 2 fraction digits.
    """
    decimal_separator = None

    for idx, c in enumerate(reversed(amount)):
        if idx >= 3:    # no more that 2 fraction digits, anything beyond is thousands separator
            break
        if c in DECIMAL_SEPS:
            decimal_separator = c
            break

    if decimal_separator is None:
        decimal_separator = DEFAULT_DECIMAL_SEP

    if amount.count(decimal_separator) >= 2:
        raise BillAggregatorException('Cannot detect decimal_separator')

    return decimal_separator
