import sys

from optimistic_reload.importlib import reload
from .utils import Package


def test_single_module(tmp_path):
    files = {
        'a.py': 'x = 1',
    }
    with Package(tmp_path, files) as package:
        import a
        assert a.x == 1
        package.write({'a.py': 'x = 2'})
        reload('a')
        assert a.x == 2


def test_import_module(tmp_path):
    files = {
        'a.py': 'x = 1',
        'b.py': 'import a',
    }
    with Package(tmp_path, files) as package:
        import b
        assert b.a.x == 1
        package.write({'a.py': 'x = 2'})
        reload('a')
        assert b.a.x == 2


def test_import_object_from_module(tmp_path):
    files = {
        'a.py': 'x = 1',
        'b.py': 'from a import x',
    }
    with Package(tmp_path, files) as package:
        import b
        assert b.x == 1
        package.write({'a.py': 'x = 2'})
        reload('a')
        assert b.x == 2
