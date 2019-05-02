import builtins
import importlib
import inspect
import sys

import networkx as nx
from networkx.algorithms import ancestors
from networkx.algorithms import topological_sort

from .utils import blue
from .utils import green
from .utils import red


__original_import__ = builtins.__import__
_dependency_graph = nx.DiGraph()


def import_and_build_dependency_graph(name, *args, **kwargs):
    module = __original_import__(name, *args, **kwargs)
    parent_frame = inspect.currentframe().f_back
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


def _ancestors_in_topological_sort_order(module_name):
    ancestral_module_names = ancestors(_dependency_graph, module_name)
    subgraph = _dependency_graph.subgraph({module_name} | ancestral_module_names)
    return list(reversed(list(topological_sort(subgraph))))


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
