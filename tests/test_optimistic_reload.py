import sys
from unittest.mock import patch

from optimistic_reload import _dependency_graph
from optimistic_reload import import_and_build_dependency_graph
from optimistic_reload import reload
from .utils import Package


def test_single_module(tmp_path_factory):
    files = {
        'a/a.py': 'x = 1',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import a.a
            assert a.a.x == 1
            package.write({'a/a.py': 'x = 2'})
            reload('a.a')
            assert a.a.x == 2


def test_single_module_from(tmp_path_factory):
    files = {
        'a/aa.py': 'import a.b; x = 1',  # TODO make this test pass without the additional import
        'a/b.py': '',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            from a import aa
            assert aa.x == 1
            package.write({'a/aa.py': 'x = 2'})
            reload('a.aa')
            assert aa.x == 2


def test_import_module(tmp_path_factory):
    files = {
        'a/a.py': 'x = 1',
        'a/b.py': 'import a.a',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import a.b
            assert a.b.a.x == 1
            package.write({'a/a.py': 'x = 2'})
            reload('a.a')
            assert a.b.a.x == 2


def test_import_object_from_module(tmp_path_factory):
    files = {
        'a/a.py': 'x = 1',
        'a/b.py': 'from a.a import x',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import a.b
            assert a.b.x == 1
            package.write({'a/a.py': 'x = 2'})
            reload('a.a')
            assert a.b.x == 2


def test_import_object_from_deeply_nested_module(tmp_path_factory):
    files = {
        'a/a.py': 'x = 1',
        'a/b.py': 'from a.a import x',
        'a/c.py': 'from a.b import x',
        'a/d.py': 'from a.c import x',
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import a.d
            assert a.d.x == 1
            package.write({'a/a.py': 'x = 2'})
            reload('a.a')
            assert a.d.x == 2


def test_run_time_imports_do_not_add_edges_to_graph(tmp_path_factory):
    files = {
        'a/a.py': 'x = 1',
        'a/b.py': (
            '''
            def f():
                import a.a
            '''),
    }
    with patch('builtins.__import__', import_and_build_dependency_graph):
        with Package(tmp_path_factory, files) as package:
            import a.b
            a.b.f()
            assert not _dependency_graph.has_edge('a.b', 'a.a')
