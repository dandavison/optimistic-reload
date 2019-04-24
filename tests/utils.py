import sys
from contextlib import contextmanager
from pathlib import Path


class Package:

    def __init__(self, root_dir, files):
        self.root_dir = root_dir
        self.write(files)

    def write(self, files):
        for relative_path, contents in files.items():
            absolute_path = self.root_dir / relative_path
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            (absolute_path.parent / '__init__.py').touch()
            absolute_path.write_text(contents)

    def activate(self):
        assert self.root_dir not in sys.path, 'Already active'
        self._original_sys_modules = set(sys.modules)
        sys.path.insert(0, str(self.root_dir))
        return self

    def deactivate(self, *args):
        sys.path.remove(str(self.root_dir))
        for new_module_name in set(sys.modules) - self._original_sys_modules:
            del sys.modules[new_module_name]
        rmtree(self.root_dir)

    __enter__ = activate
    __exit__ = deactivate
