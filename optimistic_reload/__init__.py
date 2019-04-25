import builtins
import importlib
import inspect
import sys

import networkx as nx
from networkx.algorithms import ancestors
from networkx.algorithms import topological_sort

__original_import__ = builtins.__import__
_dependency_graph = nx.DiGraph()


def import_and_build_dependency_graph(name, *args, **kwargs):
    child_module = __original_import__(name, *args, **kwargs)
    child_module_name = child_module.__name__
    caller = inspect.currentframe().f_back
    parent_module_name = caller.f_globals.get('__name__')
    _dependency_graph.add_edge(parent_module_name, child_module_name)
    return child_module


def _ancestors_in_topological_sort_order(module_name):
    ancestral_module_names = ancestors(_dependency_graph, module_name)
    subgraph = _dependency_graph.subgraph({module_name} | ancestral_module_names)
    return reversed(list(topological_sort(subgraph)))


def reload(module_name):
    for ancestral_module_name in _ancestors_in_topological_sort_order(module_name):
        importlib.reload(sys.modules[ancestral_module_name])
