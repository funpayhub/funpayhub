from typing import Any
import re
import csv
from io import StringIO
from collections.abc import Generator


KEY_RE = re.compile(r'(?<!\$)\$[a-zA-Zа-яА-Я0-9-_.]+')


def extract_calls(text: str, /) -> Generator[tuple[str, list[Any]], None, None]:
    for key in KEY_RE.finditer(text):
        start, end = key.start(), key.end()-1
        if len(text) <= end+1 or text[end+1] != '<':
            yield text[start+1:end+1], []
            continue

        args = [_ for _ in parse_args(text, end+1)]
        yield text[start+1:end+1], args


def parse_args(text: str, args_start: int) -> Generator[Any, None, None]:
    quote_opened = False
    if text[args_start] != '<':
        raise ValueError('Expected <')  # todo: parsing error

    curr_arg_index = curr_index = args_start + 1  # excluding '<'

    while True:
        index = curr_index
        curr_index += 1

        try:
            sym = text[index]
        except IndexError:
            raise ValueError('Unexpected end of text') # todo: parsing error

        if sym == '"' and text[index-1] != '\\':
            quote_opened = not quote_opened

        elif sym == '<' and not quote_opened:
            raise ValueError("Unexpected <") # todo: parsing error

        elif sym == '>' and not quote_opened:
            if curr_arg_index == index:
                return
            yield evaluate_type(text[curr_arg_index:index].strip())
            return

        elif sym == ',' and not quote_opened:
            if index == curr_arg_index:  # ,,
                raise ValueError("Unexpected ,")

            yield evaluate_type(text[curr_arg_index:index].strip())
            curr_arg_index = index + 1


def evaluate_type(arg: str) -> Any:
    if arg.startswith('"'):
        return arg[1:-1].replace('\\"', '"')
    elif arg.startswith('\\'):
        return arg.replace('\\"', '"')
    elif arg == 'True':
        return True
    elif arg == 'False':
        return False
    elif arg == 'None':
        return None
    elif arg.isnumeric():
        return int(arg)
    try:
        return float(arg)
    except ValueError:
        return arg

text = """$for_text This is my text with some formatters like $my_formatter and $parametrized_formatter<text arg1, "text arg 2 with \\"<>\\"", 123, True, False, None>
$$this_formatter should not work as well as $$this<arg1, True, arg3>,
but $this_one<some_arg1, some_text, 123, 321>, is OK!"""

args_str = '<arg1, arg2, "text arg3", 123>'


def main():
    return [i for i in extract_calls(text)]

if __name__ == '__main__':
    import timeit

    print(text)
    print(main())