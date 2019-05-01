import os

from setuptools import find_packages
from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as fp:
    long_description = fp.read()


setup(
    name='optimistic-reload',
    url='https://github.com/dandavison/optimistic-reload',
    version=open(os.path.join(os.path.dirname(__file__), 'version.txt')).read().strip(),
    author='Dan Davison',
    author_email='dandavison7@gmail.com',
    description="A python reloader experiment",
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'clint',
        'networkx',
    ],
    tests_requires=[
        'pytest',
    ],
)
