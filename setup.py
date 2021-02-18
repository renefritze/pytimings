#!/usr/bin/env python3

"""The setup script."""

from setuptools import setup, find_packages
import sys
import os

sys.path.append(os.path.dirname(__file__))
import dependencies
import versioneer

tests_require = dependencies.ci_requires
install_requires = dependencies.install_requires
setup_requires = dependencies.setup_requires()
install_suggests = dependencies.install_suggests

with open('README.rst') as readme_file:
    readme = readme_file.read()
with open('HISTORY.rst') as history_file:
    history = history_file.read()

setup(
    author="René Fritze",
    author_email='coding@fritze.me',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="MPI Aware section timings",
    entry_points={
        'console_scripts': [
            'pytimings=pytimings.cli:main',
        ],
    },
    tests_require=tests_require,
    install_requires=install_requires,
    extras_require=dependencies.extras(),
    license="BSD license",
    long_description=readme + '\n\n' + history + '\n\n',
    include_package_data=True,
    keywords='pytimings',
    name='pytimings',
    packages=find_packages(include=['pytimings', 'pytimings.*']),
    url='https://github.com/WWU-AMM/pytimings',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    zip_safe=False,
)
