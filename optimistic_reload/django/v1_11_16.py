import sys
from contextlib import ExitStack
from contextlib import contextmanager
from importlib import import_module
from importlib import reload
from unittest import mock

import optimistic_reload


# django.urls.resolvers:RegexURLResolver.urlconf_module
# Copied from Django 1.11.16 3d0344dc40 and modified to
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


# django.urls.resolvers:RegexURLResolver.url_patterns
# Copied from Django 1.11.16 3d0344dc40 and modified to
# (a) remove the cached property decorator
@property
def url_patterns(self):
    # urlconf_module might be a valid set of patterns, so we default to it
    patterns = getattr(self.urlconf_module, "urlpatterns", self.urlconf_module)
    try:
        iter(patterns)
    except TypeError:
        from django.core.exceptions import ImproperlyConfigured
        msg = (
            "The included URLconf '{name}' does not appear to have any "
            "patterns in it. If you see valid patterns in the file then "
            "the issue is probably caused by a circular import."
        )
        raise ImproperlyConfigured(msg.format(name=self.urlconf_name))
    return patterns


objects_to_patch = [
    ('django.urls.resolvers.RegexURLResolver.urlconf_module', urlconf_module),
    ('django.urls.resolvers.RegexURLResolver.url_patterns', url_patterns),
    ('builtins.__import__', optimistic_reload.import_and_build_dependency_graph),
]


@contextmanager
def apply_patches():
    with ExitStack() as stack:
        yield [stack.enter_context(mock.patch(target, new))
               for target, new in objects_to_patch]
