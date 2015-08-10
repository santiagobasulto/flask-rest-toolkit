import os

from setuptools import setup
from setuptools.command.test import test as TestCommand

import flask_rest_toolkit
version = flask_rest_toolkit.__version__
project_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
project_url = 'http://github.com/santiagobasulto/{project_name}'.format(
    project_name=project_name)


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
        #import here, cause outside the eggs aren't loaded
        import sys, pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name=flask_rest_toolkit.__title__,
    version=version,
    description=flask_rest_toolkit.__description__,
    url=project_url,
    download_url="{url}/tarball/{version}".format(
        url=project_url, version=version),
    author='Santiago Basulto',
    author_email='santiago.basulto@gmail.com',
    license='MIT',
    packages=['flask_rest_toolkit'],
    maintainer='Santiago Basulto',
    install_requires=[
        'Flask==0.10.1'
    ],
    tests_require=[
        'cov-core==1.15.0',
        'coverage==3.7.1',
        'py==1.4.30',
        'pytest==2.7.2',
        'pytest-cov==2.0.0',
        'six==1.9.0',
        'mock==1.0.1'
    ],
    zip_safe=True,
    cmdclass={'test': PyTest},
)
