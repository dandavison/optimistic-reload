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
    # Do not add edges for run time imports in function bodies.
    # - For an import in a function, frame.f_code.co_name is the function name (or '<lambda>').
    # - For a top-level import, frame.f_code.co_name is '<module>'.
    # TODO: Is there a more official API to use?
    if parent_frame.f_code.co_name == '<module>':
        parent_module_name = parent_frame.f_globals.get('__name__')
        _dependency_graph.add_edge(parent_module_name, name)

    return module


def _ancestors_in_topological_sort_order(module_name):
    ancestral_module_names = ancestors(_dependency_graph, module_name)
    subgraph = _dependency_graph.subgraph({module_name} | ancestral_module_names)
    try:
        return list(reversed(list(topological_sort(subgraph))))
    except Exception as ex:
        from networkx.drawing.nx_pydot import write_dot
        file = '/tmp/optimistic-reload.dot'
        write_dot(subgraph, file)
        print(red(f'optimistic-reload: error: graph written to: {file}'))
        raise



def reload(module_name):
    if module_name not in _dependency_graph:
        print(red(f'optimistic-reload: error: not in graph: {module_name}'))
        return
    else:
        ancestral_module_names = _ancestors_in_topological_sort_order(module_name)

    print(blue(f'optimistic-reload: reloading: {ancestral_module_names}'))

    for ancestral_module_name in ancestral_module_names:
        try:
            importlib.reload(sys.modules[ancestral_module_name])
        except Exception as ex:
            print(red((f'optimistic-reload: '
                       f'error while attempting reload({ancestral_module_name}): '
                       f'{ex.__class__.__name__}({ex})')))

    print(green(f'optimistic-reload: reloaded ancestors of {module_name}'))
    print('\n')
