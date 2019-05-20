from optimistic_reload import _dependency_graph
from optimistic_reload import reload

from .utils import _test_package


def test_single_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
    }
    with _test_package(tmp_path_factory, files) as package:
        import a
        assert a.x == 1
        package.write({'a.py': 'x = 2'})
        assert reload('a')
        assert a.x == 2


def test_single_module_from(tmp_path_factory):
    files = {
        'a/aa.py': 'x = 1',
    }
    with _test_package(tmp_path_factory, files) as package:
        from a import aa
        assert aa.x == 1
        package.write({'a/aa.py': 'x = 2'})
        assert reload('a.aa')
        assert aa.x == 2


def test_import_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'import a',
    }
    with _test_package(tmp_path_factory, files) as package:
        import b
        assert b.a.x == 1
        package.write({'a.py': 'x = 2'})
        assert reload('a')
        assert b.a.x == 2


def test_import_object_from_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'from a import x',
    }
    with _test_package(tmp_path_factory, files) as package:
        import b
        assert b.x == 1
        package.write({'a.py': 'x = 2'})
        assert reload('a')
        assert b.x == 2


def test_import_module_from_module(tmp_path_factory):
    files = {
        'a/a.py': 'x = 1',
        'b.py': 'from a import a; x = a.x',
    }
    with _test_package(tmp_path_factory, files) as package:
        import b
        assert _dependency_graph.has_edge('b', 'a.a')
        assert not _dependency_graph.has_edge('a', 'a.a')
        assert b.x == 1
        package.write({'a/a.py': 'x = 2'})
        assert reload('a.a')
        assert b.x == 2


def test_import_object_from_deeply_nested_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'from a import x',
        'c.py': 'from b import x',
        'd.py': 'from c import x',
    }
    with _test_package(tmp_path_factory, files) as package:
        import d
        assert d.x == 1
        package.write({'a.py': 'x = 2'})
        assert reload('a')
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
    with _test_package(tmp_path_factory, files) as package:
        import b
        b.f()
        assert not _dependency_graph.has_edge('b', 'a')


def test_non_circular_import(tmp_path_factory):
    files = {
        'a/a.py': 'from a import b',
        'a/b.py': '',
        'b.py': 'from a import a',
    }
    with _test_package(tmp_path_factory, files) as package:
        import a.a
        import b
        assert reload('a.b')
