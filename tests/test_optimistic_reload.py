from optimistic_reload import _dependency_graph
from optimistic_reload import reload

from .utils import _test_context


def test_single_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
    }
    with _test_context(tmp_path_factory, files) as ctx:
        import a
        assert a.x == 1
        ctx.package.write({'a.py': 'x = 2'})
        reload('a')
        assert a.x == 2


def test_single_module_from(tmp_path_factory):
    files = {
        'a/aa.py': 'x = 1',
    }
    with _test_context(tmp_path_factory, files) as ctx:
        from a import aa
        assert aa.x == 1
        ctx.package.write({'a/aa.py': 'x = 2'})
        reload('a.aa')
        assert aa.x == 2


def test_import_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'import a',
    }
    with _test_context(tmp_path_factory, files) as ctx:
        import b
        assert b.a.x == 1
        ctx.package.write({'a.py': 'x = 2'})
        reload('a')
        assert b.a.x == 2


def test_import_object_from_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'from a import x',
    }
    with _test_context(tmp_path_factory, files) as ctx:
        import b
        assert b.x == 1
        ctx.package.write({'a.py': 'x = 2'})
        reload('a')
        assert b.x == 2


def test_import_module_from_module(tmp_path_factory):
    files = {
        'a/a.py': 'x = 1',
        'b.py': 'from a import a',
    }
    with _test_context(tmp_path_factory, files) as ctx:
        import b
        assert _dependency_graph.has_edge('b', 'a')
        assert _dependency_graph.has_edge('a', 'a.a')
        assert b.a.x == 1
        ctx.package.write({'a/a.py': 'x = 2'})
        reload('a.a')
        assert b.a.x == 2


def test_import_object_from_deeply_nested_module(tmp_path_factory):
    files = {
        'a.py': 'x = 1',
        'b.py': 'from a import x',
        'c.py': 'from b import x',
        'd.py': 'from c import x',
    }
    with _test_context(tmp_path_factory, files) as ctx:
        import d
        assert d.x == 1
        ctx.package.write({'a.py': 'x = 2'})
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
    with _test_context(tmp_path_factory, files) as ctx:
        import b
        b.f()
        assert not _dependency_graph.has_edge('b', 'a')
