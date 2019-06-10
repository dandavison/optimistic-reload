import sys
from contextlib import ExitStack
from contextlib import contextmanager
from importlib import import_module
from importlib import reload
from unittest import mock

from django.urls import resolvers

import optimistic_reload


class RegexURLResolver(resolvers.RegexURLResolver):
    """
    Modification of Django's RegexURLResolver to prevent retrieval of stale URLs from the cache
    that Django uses for `reverse`.
    """

    # For `urlconf_module`:
    # (a) reload the module if it has already been imported
    # (b) remove the cached property decorator
    @property
    def urlconf_module(self):
        if isinstance(self.urlconf_name, str):
            module = sys.modules.get(self.urlconf_name)
            if module:
                return reload(module)
            else:
                return import_module(self.urlconf_name)
        else:
            return self.urlconf_name

    # Replace `cached_property` with `property` decorator on `url_patterns`
    url_patterns = property(resolvers.RegexURLResolver.url_patterns.func)


objects_to_patch = [
    ('django.urls.resolvers.RegexURLResolver', RegexURLResolver),
    ('builtins.__import__', optimistic_reload.import_and_build_dependency_graph),
]


@contextmanager
def apply_patches():
    with ExitStack() as stack:
        yield [stack.enter_context(mock.patch(target, new))
               for target, new in objects_to_patch]
