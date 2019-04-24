Suppose you're working on backend code for a web application. You're running the development server locally, you edit some of the code files, and you want the next response from the server to reflect the changes you made.

Python web frameworks such as [Django](https://github.com/django/django/blob/master/django/utils/autoreload.py#L211) and [Flask](https://github.com/pallets/werkzeug/blob/master/src/werkzeug/_reloader.py#L176) respond to on-disk changes by restarting the server process. This is reasonable: re-importing the whole codebase from scratch guarantees that the state of the new server process matches the code.

However, for large projects this can be slow. It would be nice if, when you change the code on disk, the necessary changes occur in memory without restarting the process. What's required for that to happen? Or at least, what's required for it to happen sufficiently often for it to be useful?

-------------------------------------------------------------------------------------------------------------------

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
