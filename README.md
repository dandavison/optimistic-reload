[![Build Status](https://travis-ci.com/dandavison/optimistic-reload.svg?branch=master)](https://travis-ci.com/dandavison/optimistic-reload)

This is an experimental hot-reloader for Python web development. It patches `__import__` so that it builds a dependency graph and, when a module has changed on disk, it consults this graph to determine which other modules should be reloaded. The code here is framework-agnostic, but I'm testing it against Django's development server.


## Introduction

Suppose you're working on backend code for a web application. You're running the development server locally, you edit some of the code files, and you want the next response from the server to reflect the changes you made.

Python web frameworks such as [Django](https://github.com/django/django/blob/master/django/utils/autoreload.py#L211) and [Flask](https://github.com/pallets/werkzeug/blob/master/src/werkzeug/_reloader.py#L176) respond to on-disk changes by restarting the server process. This is reasonable: re-importing the whole codebase from scratch guarantees that the state of the new server process matches the code.

However, for large codebases this can be slow (20 seconds or more). It would be nice if, when you change the code on disk, the necessary changes occur in memory without restarting the process. What's required for that to happen? Or at least, what's required for it to happen sufficiently reliably for it to be useful?


## Findings
In general, this seems successful. For many HTTP endpoints, on-disk changes result in the appropriate in-memory changes and one can enjoy much faster reloads (e.g. 20 sec becomes 1 sec).


## Challenges

If a class definition is changed and reloaded, extant instances do not acquire the methods and attributes of the new class. This is a fact of the language. A consequence is that this sort of hot-reloading may be of limited use in an interactive shell/notebook sesssion where instances commonly persist across reloads.

However, there are grounds for optimism. Web server code, simplistically, often looks like this:
```python
def http_request_handler(request):
    objects = instantiate_some_objects(request)
    return make_http_response(objects)
```
When that is so, there is no problem: the instances do not persist between HTTP requests (i.e. across reloads). But if instances are cached and persist across HTTP requests, then we could end up in a situation where some instances are using a stale class definition. One solution is to clear such caches on reload. If hot-reload is actually valuable, then another might be to write hot-reload-friendly code.

Similarly, in Python the "registry pattern" is sometimes used in metaclasses so that classes are automatically registered in some way whenever the class definition is executed. Replacing the registry entry with the new class definition might well be acceptable/appropriate. However, sometimes authors will raise an exception on an attempt to set the same key twice in the registry.


-------------------------------------------------------------------------------------------------------------------

## Determining what needs to be reloaded

Let's take a simple case.


- `myproject/urls.py`:
```python
from myproject.myviews import myview
urlpatterns = [
    path('/myview/', myview),
]
```
- `myproject/myviews.py`:
```python
def myview(request):
    return HttpResponse('Hello World')
```


Now, we have changed `myproject/myviews.py` on disk. We need to:

1. Re-import the `myproject/views.py` file, replacing the module object `sys.modules['myproject.views']` with the new module object.
2. Find the reference to the function object named `myview` in the `myproject.urls` module namespace and replace it with a reference to the new function object taken from the `myproject.views` module namespace.

-------------------------------------------------------------------------------------------------------------------

In general, consider a graph with a node for every module in the project. For all pairs `(a, b)` of modules, an edge exists from module `a` to module `b` if `a` imports `b` (whether by `import b` or by `from b import some_object`). This graph is a DAG (python will not start if there are cycles in it).


Now consider module `m` which has been changed on disk. The set of modules which might contain a reference to an object defined in `m` is the set of ancestors<sup>1</sup> of `m`


-------------------------------------------------------------------------------------------------------------------

<sup>1</sup> Definition: the _ancestors_ of a node `v` in a directed graph is the set of all nodes `u` such that a directed path exists from `u` to `v`.
