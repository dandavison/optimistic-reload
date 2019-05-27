import sys
import traceback

from clint.textui import colored


red = lambda s: colored.red(s, bold=True)
green = lambda s: colored.green(s, bold=True)
blue = lambda s: colored.blue(s, bold=True)


def log_error(msg):
    print('\n'.join(traceback.format_stack()), file=sys.stderr)
    print(red(msg), file=sys.stderr)
