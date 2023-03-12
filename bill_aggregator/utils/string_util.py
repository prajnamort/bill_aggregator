import unicodedata


PLACEHOLDER = '...'
PLACEHOLDER_POS = -1
WRAP_PUNCS = '!,-.:;?'


class Align:
    LEFT = 'left'
    RIGHT = 'right'

    ALL = [LEFT, RIGHT]


def char_width(char):
    if unicodedata.east_asian_width(char) in 'WF':
        return 2
    return 1


def string_width(string):
    return sum(char_width(c) for c in string)


def shorten_string(string, width, placeholder=PLACEHOLDER, placeholder_pos=PLACEHOLDER_POS):
    if string_width(string) <= width:
        return string

    reverse = False
    if placeholder_pos < 0:
        reverse = True
        string = string[::-1]
        placeholder_pos = abs(placeholder_pos) - 1
    assert placeholder_pos + len(placeholder) <= width

    # left side of placeholder
    result = ''
    cur_width = 0
    for char in string:
        cur_width += char_width(char)
        if cur_width > placeholder_pos:
            break
        result += char
    # placeholder
    result += placeholder[::-1] if reverse else placeholder
    # right side of placeholder
    right_width = width - string_width(result)
    right_str = ''
    cur_width = 0
    for char in string[::-1]:
        cur_width += char_width(char)
        if cur_width > right_width:
            break
        right_str += char
    result += right_str[::-1]

    if reverse:
        result = result[::-1]
    return result


def fit_string(string, width, align=Align.LEFT,
               placeholder=PLACEHOLDER, placeholder_pos=PLACEHOLDER_POS):
    if string_width(string) > width:
        string = shorten_string(
            string=string,
            width=width,
            placeholder=placeholder,
            placeholder_pos=placeholder_pos)

    assert align in Align.ALL
    if align == Align.LEFT:
        return string + ' ' * (width - string_width(string))
    else:
        return ' ' * (width - string_width(string)) + string


def wrap_string(string, width=70, long_word_tolerance=20):
    assert width >= 1
    assert long_word_tolerance >= 1
    assert width > long_word_tolerance, 'width > long_word_tolerance'

    if string_width(string) <= width:
        return [string]

    cur_pos = 0
    cur_width = 0
    for char in string:
        cur_width += char_width(char)
        if cur_width > width:
            break
        cur_pos += 1

    split_pos = cur_pos
    long_word = 0
    for pos in range(cur_pos, 1, -1):
        cur_char = string[pos-1]
        next_char = string[pos]
        if (next_char.isspace() or char_width(next_char) == 2
            or cur_char.isspace() or char_width(cur_char) == 2 or cur_char in WRAP_PUNCS):
            split_pos = pos
            break
        long_word += char_width(cur_char)
        if long_word > long_word_tolerance:
            break

    first_line = string[:split_pos]
    rest_lines = wrap_string(
        string=string[split_pos:],
        width=width,
        long_word_tolerance=long_word_tolerance)
    return [first_line, *rest_lines]
