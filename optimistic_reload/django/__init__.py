from contextlib import contextmanager

import optimistic_reload


@contextmanager
def apply_patches():
    from django import  get_version
    django_version = get_version()
    if django_version == '1.11.16':
        from optimistic_reload.django import v1_11_16
        with v1_11_16.apply_patches():
            yield
    else:
        raise Exception(f'No optimistic-reload patches for Django version {django_version}')


def file_changed_signal_handler(sender, **kwargs):
    return optimistic_reload.reload_file(kwargs['file_path'].as_posix())
