import builtins
import importlib
import inspect
import sys
from collections import defaultdict
from pprint import pprint


__original_import__ = builtins.__import__
_dependency_graph = defaultdict(set)


def import_and_build_dependency_graph(name, *args, **kwargs):
    child_module = __original_import__(name, *args, **kwargs)
    if hasattr(child_module, '__file__'):
        child_module_name = child_module.__name__
        _dependency_graph[child_module.__file__].add(child_module_name)
        caller = inspect.currentframe().f_back
        parent_module_name = caller.f_globals.get('__name__')
        _dependency_graph[child_module.__file__].add(parent_module_name)
    return child_module


def reload(module_name):
    module = sys.modules[module_name]
    path = module.__file__
    module_names_to_reload = {module_name} | _dependency_graph.get(path, set())
    for module_name in module_names_to_reload:
        importlib.reload(sys.modules[module_name])
