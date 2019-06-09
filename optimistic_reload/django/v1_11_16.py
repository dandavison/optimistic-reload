from contextlib import ExitStack
from contextlib import contextmanager
from unittest import mock

import optimistic_reload


objects_to_patch = [
    ('builtins.__import__', optimistic_reload.import_and_build_dependency_graph),
]


@contextmanager
def apply_patches():
    with ExitStack() as stack:
        yield [stack.enter_context(mock.patch(target, new))
               for target, new in objects_to_patch]
