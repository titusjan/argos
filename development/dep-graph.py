#!/usr/bin/env python3
""" Draws a dependency graphs from the conda-lock loc file.

    Uses the graphviz package from python. Install with:
    $> mamba install python-graphviz

    The lock files should be created with conda-lock (https://conda.github.io/conda-lock/)
    For instance:
    $> conda-lock -p linux-64 -f pyproject.toml

    Note that I did not get it to work with exdir, so you need to comment that line out
    in the pyproject.toml file.

    Platform independent pacakges are drawn a ellipses. Platform dependent packages are boxes.
"""
import copy
import enum
import os.path
import sys

import graphviz
import yaml

# If false, dependencies to '__glibc' are NOT plotted. This makes the graph much smaller
# and more readable. The __glibc is an implicit package anyway (there is no actual glibc package)
# Note that the Windows equivalent of glibc (ucrt) *is* installed as a package.
SHOW_GLIBC = False

GLIBC = '__glibc'
UCRT = 'ucrt'     # Windows equivalent of GLIBC



FILL_COLORS = {
    'main': 'white',
    'pyqt5': 'lightgreen',
    'all-formats': 'lightblue',
}

class Architecture(enum.StrEnum):
    NO_ARCH = 'no_arch'
    LINUX = 'linux'
    WINDOWS = 'windows'


def load_lock_file(file_name):
    with open(file_name, 'r') as lock_file:
        return yaml.safe_load(lock_file)


def find_implicit_packages(packages: list) -> list[str]:
    """ Find dependencies that are not an actual package (__glibc, __unix, etc.)
    """
    packages_names = [pkg['name'] for pkg in packages]

    implicit_packages = []
    for pkg in packages:
        for dep in pkg['dependencies']:
            if dep not in packages_names and dep not in implicit_packages:
                #print(f"Dependency {dep} not in package names")
                implicit_packages.append(dep)

    return implicit_packages

def merge_duplicate_packages(packages: list) -> list[dict]:
    """ Returns package list where packages that occur in multiple categories are merged.

        Returns a copy of the list.
        The 'category' item is replaced by a 'categories' item in every dict in the list.
    """
    result = []
    pkg_dict = {}  # Temporary dict to look up packages
    for pkg in packages:
        name = pkg['name']
        if name in pkg_dict:
            print(f"Duplicate package name '{name}'")
            pkg_old = pkg_dict[name]
            assert pkg['version'] == pkg_old['version']
            assert pkg['dependencies'] == pkg_old['dependencies']
            assert pkg['hash']['md5'] == pkg_old['hash']['md5']
            pkg_old['categories'].append(pkg['category'])
        else:
            pkg['categories'] = [pkg['category']]
            del pkg['category']
            result.append(pkg)
            pkg_dict[name] = pkg

    return result


def set_package_architecture(packages: list) -> list[dict]:
    """ Sets the packages kind for all pakages in the list.

        Returns a copy of the list.
        Will add the 'arch' key to all package dicts in the list
    """
    result = []
    for pkg in packages:
        url = pkg['url']
        if url.startswith('https://conda.anaconda.org/conda-forge/noarch'):
            pkg['arch'] = Architecture.NO_ARCH
        elif url.startswith('https://conda.anaconda.org/conda-forge/linux-64'):
            pkg['arch'] = Architecture.LINUX
        elif url.startswith('https://conda.anaconda.org/conda-forge/win-64'):
            pkg['arch'] = Architecture.WINDOWS
        else:
            raise ValueError(f"Unknown architecture for URL: {url}")
        result.append(pkg)
    return result



def render_packages(packages: list):

    dot = graphviz.Digraph(name='Dependencies')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box', style='filled', gradientangle='270')

    implicit_packages = find_implicit_packages(packages)

    # Add nodes for implicit packages. Not strictly necessary since GraphVis will draw them anyway.
    for pkg_name in implicit_packages:
        if SHOW_GLIBC or pkg_name != GLIBC:
            dot.node(pkg_name)

    for pkg in packages:
        name = pkg['name']

        #category = pkg['category']

        if name == 'python':
            fill_color = 'pink'
        elif name in implicit_packages:
            fill_color = 'lightgrey'
        else:
            colors = [FILL_COLORS[cat] for cat in pkg['categories']]
            fill_color = ':'.join(colors) # Gradient fill if multiple categories.

        label = f"{name}\n{pkg['version']}"

        label_deps = [] # Dependencies added to the label
        if GLIBC in pkg['dependencies']:
            label_deps.append('glibc')
        if UCRT in pkg['dependencies']:
            label_deps.append('ucrt')
        if 'python' in pkg['dependencies']:
            label_deps.append('python')

        if label_deps:
            label += f"\n\n({','.join(label_deps)})"

        dot.node(name,
                 label=label,
                 fillcolor=fill_color,
                 shape='ellipse' if pkg['arch'] == Architecture.NO_ARCH else 'box')

    for pkg in packages:
        for dep, version in pkg['dependencies'].items():
            if SHOW_GLIBC or dep != GLIBC:
                dot.edge(pkg['name'], dep)

    return dot



def main():
    input_file = sys.argv[1]
    dct = load_lock_file(input_file)

    packages = dct['package']
    packages = set_package_architecture(packages)
    packages = merge_duplicate_packages(packages)

    print('')
    print(f"Number of unique packages: {len(packages)}")
    for pkg in packages:
        categories = ','.join(pkg['categories'])
        print(f"{pkg['name']:25s}  {pkg['version']:15s} {categories:20s} "
              f"{pkg['arch']:10s} {pkg['dependencies']}")
    print('-' * 100)

    dot = render_packages(packages)

    base_name = os.path.basename(input_file)
    stem_name = os.path.splitext(base_name)[0]
    output_file = f"{stem_name}.dot"
    dot.name = stem_name
    dot.comment = f"Dependency table of: {input_file}"

    # print(dot.source)

    dot.render(filename=output_file, cleanup=True)
    dot.view()


if __name__ == '__main__':
    main()
