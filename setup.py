import os
import ast

from setuptools import setup
from setuptools.command.test import test as TestCommand

VALUES = {
    '__version__': None,
    '__title__': None,
    '__description__': None
}

with open('flask_rest_toolkit/__init__.py', 'r') as f:
    tree = ast.parse(f.read())
    for node in tree.body:
        if node.__class__ != ast.Assign:
            continue
        target = node.targets[0]
        if target.id in VALUES:
            VALUES[target.id] = node.value.s

if not all(VALUES.values()):
    raise RuntimeError("Can't locate values to init setuptools hook.")


version = VALUES['__version__']


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ["--cov", "flask_rest_toolkit", "tests/"]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import sys
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def read_requirements(file_name):
    with open(file_name, 'r') as fp:
        return [l.strip() for l in fp if l.strip() and not l.startswith('-r')]


setup(
    name=VALUES['__title__'],
    version=version,
    description=VALUES['__description__'],
    url='https://github.com/santiagobasulto/slack-cli',
    author='Santiago Basulto',
    author_email='santiago@rmotr.com',
    license='MIT',
    packages=['flask_rest_toolkit'],
    maintainer='Santiago Basulto',
    install_requires=read_requirements('requirements.txt'),
    tests_require=read_requirements('dev-requirements.txt'),
    zip_safe=True,
    cmdclass={'test': PyTest},
)
