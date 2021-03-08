#!/usr/bin/env python3

# DO NOT use any python features here that require 3.6 or newer


def setup_requires():
    # setuptools pin in accordance with numpy: https://github.com/numpy/numpy/pull/17000, see also https://github.com/pypa/setuptools/pull/2260 https://github.com/pypa/setuptools/pull/2259
    return [
        'psutil',
        'setuptools>=40.8.0,<49.2.0',
        'wheel',
        'pytest-runner>=2.9',
        'packaging',
    ]


install_requires = ['packaging', 'typer'] + setup_requires()
install_suggests = {
    'matplotlib': 'needed for error plots in demo scipts',
    'mpi4py': 'needed for global data operations',
}
doc_requires = [
    'sphinx>=3.3',
    'matplotlib',
    'python-slugify',
    'sphinx-material',
    'sphinx-autoapi>=1.7',
] + install_requires
ci_requires = [
    'pytest',
    'pytest-cov',
    'pytest-xdist',
    'check-manifest',
    'black',
    'pre-commit',
    'autopep8',
    'pytest-pycharm',
    'readme_renderer[md]',
    'rstcheck',
    'codecov',
    'twine',
    'pytest-memprof',
    'pytest-regressions',
    'pytest-datadir',
    'pytest-timeout',
    'docutils',
]
# these don't go into the pip extras
optional_requirements_file_only = []


def strip_markers(name):
    for m in ';<>=':
        try:
            i = name.index(m)
            name = name[:i].strip()
        except ValueError:
            continue
    return name


def extras():
    import pkg_resources
    import itertools

    def _candidates(blocklist):
        # skip those which aren't needed in our current environment (py ver, platform)
        for pkg in set(itertools.chain(doc_requires, install_suggests.keys())):
            if pkg in blocklist:
                continue
            try:
                marker = next(pkg_resources.parse_requirements(pkg)).marker
                if marker is None or marker.evaluate():
                    yield pkg
            except pkg_resources.RequirementParseError:
                # try to fake a package to get the marker parsed
                stripped = strip_markers(pkg)
                fake_pkg = 'pip ' + pkg.replace(stripped, '')
                try:
                    marker = next(pkg_resources.parse_requirements(fake_pkg)).marker
                    if marker is None or marker.evaluate():
                        yield pkg
                except pkg_resources.RequirementParseError:
                    continue

    # blocklisted packages need a (minimal) compiler setup
    # - nbresuse, pytest-memprof depend on psutil which has no wheels
    return {
        'ci': ci_requires,
        'docs': doc_requires,
        'full': list(install_suggests.keys()) + ci_requires + doc_requires,
    }


toml_tpl = '''
[tool.black]
line-length = 120
skip-string-normalization = true

[build-system]
requires = {0}
build-backend = "setuptools.build_meta"
'''
if __name__ == '__main__':
    note = '# This file is autogenerated. Edit dependencies.py instead'
    print(' '.join([i for i in install_requires + list(install_suggests.keys())]))
    import os
    import itertools

    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'), 'wt') as req:
        req.write(note + '\n')
        for module in sorted(set(itertools.chain(install_requires, setup_requires()))):
            req.write(module + '\n')
    with open(os.path.join(os.path.dirname(__file__), 'requirements-optional.txt'), 'wt') as req:
        req.write(note + '\n')
        req.write('-r requirements.txt\n')
        req.write('-r requirements-ci.txt\n')
        for module in sorted(
            set(itertools.chain(optional_requirements_file_only, doc_requires, install_suggests.keys()))
        ):
            req.write(module + '\n')
    with open(os.path.join(os.path.dirname(__file__), 'requirements-ci.txt'), 'wt') as req:
        req.write('-r requirements.txt\n')
        req.write(note + '\n')
        for module in sorted(ci_requires):
            req.write(module + '\n')
    with open(os.path.join(os.path.dirname(__file__), 'pyproject.toml'), 'wt') as toml:
        toml.write(note)
        toml.write(toml_tpl.format(str(setup_requires())))
