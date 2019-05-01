import sys
from unittest.mock import patch

from optimistic_reload import _dependency_graph
from optimistic_reload import import_and_build_dependency_graph
from optimistic_reload import reload
from .utils import Package


def test_single_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import a
            assert a.x == 1
            package.write({'a.py': 'x = 2'})
            reload('a')
            assert a.x == 2


def test_import_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'import a',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import b
            assert b.a.x == 1
            package.write({'a.py': 'x = 2'})
            reload('a')
            assert b.a.x == 2


def test_import_object_from_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'from a import x',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import b
            assert b.x == 1
            package.write({'a.py': 'x = 2'})
            reload('a')
            assert b.x == 2


def test_import_object_from_deeply_nested_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'from a import x',
        'c.py': 'from b import x',
        'd.py': 'from c import x',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import d
            assert d.x == 1
            package.write({'a.py': 'x = 2'})
            reload('a')
            assert d.x == 2


def test_run_time_imports_do_not_add_edges_to_graph(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': (
            '''
            def f():
                import a
            '''),
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import b
            b.f()
            assert not _dependency_graph.has_edge('b', 'a')
