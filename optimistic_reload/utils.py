import subprocess
import sys
import traceback

from clint.textui import colored


red = lambda s: colored.red(s, bold=True)
green = lambda s: colored.green(s, bold=True)
blue = lambda s: colored.blue(s, bold=True)


LOGFILE = open('/tmp/optimistic-reload.log', 'a')


def log(msg, **kwargs):
    print(msg, file=LOGFILE, flush=True)
    if kwargs.get('notify', False):
        notify(msg)


def log_error(msg):
    print('\n'.join(traceback.format_stack()), file=LOGFILE, flush=True)
    print(red(msg), file=LOGFILE, flush=True)
    notify(msg)


def notify(msg):
    # TODO: Make this user-configurable
    subprocess.call([
        'terminal-notifier',
        '-title', 'optimistic-reload',
        '-message', msg,
    ])

