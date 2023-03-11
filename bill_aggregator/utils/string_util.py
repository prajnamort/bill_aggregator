import unicodedata


PLACEHOLDER = '...'
PLACEHOLDER_POS = -1


class Align:
    LEFT = 'left'
    RIGHT = 'right'

    ALL = [LEFT, RIGHT]


def char_width(char):
    if unicodedata.east_asian_width(char) in 'WF':
        return 2
    return 1


def string_width(string):
    # return string len including double count for double width characters
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
