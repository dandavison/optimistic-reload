import builtins


__all__ = [__import__]

__builtins__import__ = builtins.__import__


def __import__(name, *args, **kwargs):
    return __builtins__import__(name, *args, **kwargs)
