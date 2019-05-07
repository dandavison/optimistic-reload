import builtins
import importlib
import inspect
import sys

import networkx as nx
from networkx.algorithms import ancestors
from networkx.algorithms import find_cycle
from networkx.algorithms import topological_sort

from .utils import blue
from .utils import green
from .utils import red


__original_import__ = builtins.__import__
_dependency_graph = nx.DiGraph()


def import_and_build_dependency_graph(name, globals=None, locals=None, fromlist=(), level=0):
    module = (
        __original_import__(name, globals=globals, locals=locals, fromlist=fromlist, level=level))
    parent_frame = inspect.currentframe().f_back
    if fromlist:
        _add_fromlist_edges(name, fromlist, module, parent_frame)
    else:
        _add_edge(parent_frame, name)
    return module


def _add_edge(parent_frame, child_module_name):
    """
    Add an edge from a parent module to a child module which the parent imports.

    Do not add edges for run time imports in function bodies, since those will not result in stale
    object references and therefore do not confer a requirement for reloading.

    However, make an exception for the test suite, since it simulates top-level imports via imports
    in the bodies of test functions.
    """
    # - For an import in a function, frame.f_code.co_name is the function name (or '<lambda>').
    # - For a top-level import, frame.f_code.co_name is '<module>'.
    # TODO: Is there a more official API to use?
    parent_module_name = parent_frame.f_globals.get('__name__')
    parent_is_module = parent_frame.f_code.co_name == '<module>'
    parent_file_name = parent_frame.f_globals.get('__file__')
    parent_is_function_in_test_suite = (parent_file_name and
                                        parent_file_name.endswith('test_optimistic_reload.py'))
    if parent_is_module or parent_is_function_in_test_suite:
        _dependency_graph.add_edge(parent_module_name, child_module_name)


def _add_fromlist_edges(module_name, fromlist, module, parent_frame):
    """
    Add edges for child modules imported as `from parent_module import child_module`.

    In cpython, such a child module is imported directly (via _call_with_frames_removed), bypassing
    __import__. Therefore we have to add edges for these imports in addition to adding edges
    corresponding to __import__ calls.

    See _handle_fromlist
    https://github.com/python/cpython/blob/0d5864fa07ab4f03188/Lib/importlib/_bootstrap.py#L1017
    """
    for imported_name in fromlist:
        if not hasattr(module, imported_name) or inspect.ismodule(getattr(module, imported_name)):
            # If the attribute didn't exist, we assume it's a module, as in _handle_fromlist.
            imported_module_name = f'{module.__name__}.{imported_name}'
            _dependency_graph.add_edge(module_name, imported_module_name)
        else:
            _add_edge(parent_frame, module_name)


def _ancestors_in_topological_sort_order(module_name):
    ancestral_module_names = ancestors(_dependency_graph, module_name)
    subgraph = _dependency_graph.subgraph(ancestral_module_names)
    try:
        sorted_nodes = topological_sort(subgraph)
    except nx.NetworkXUnfeasible as ex:
        try:
            cycle = find_cycle(subgraph)
        except Exception as ex:
            print(red(f'find_cycle: error: {ex.__class__.__name__}({ex})'), file=sys.stderr)
        else:
            print(red(f'cycle: {cycle}'))
        finally:
            raise
    else:
        return list(reversed(list(sorted_nodes)))


def reload(module_name):
    module = importlib.reload(sys.modules[module_name])
    if module_name not in _dependency_graph:
        print(red(f'optimistic-reload: error: not in graph: {module_name}'), file=sys.stderr)
        return None

    try:
        ancestral_module_names = _ancestors_in_topological_sort_order(module_name)
    except Exception as ex:
        print(red(f'optimistic-reload: error: {ex.__class__.__name__}({ex})'), file=sys.stderr)
        return None

    print(blue(f'optimistic-reload: reloading {module_name} '
               f'and ancestors: {ancestral_module_names}'))

    for ancestral_module_name in ancestral_module_names:
        try:
            importlib.reload(sys.modules[ancestral_module_name])
        except Exception as ex:
            print(red(f'optimistic-reload: '
                      f'error while attempting reload({ancestral_module_name}): '
                      f'{ex.__class__.__name__}({ex})'), file=sys.stderr)
            return None

    print(green(f'optimistic-reload: reloaded ancestors of {module_name}\n'))
    return module
