"""Setup configuration and dependencies for the pyatop library."""

import os
import setuptools

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))


def _find_version() -> str:
    """Locate semantic version from a text file in a compatible format with setuptools."""
    # Do not import the module within the library, as this can cause an infinite import. Read manually.
    init_file = os.path.join(ROOT_DIR, 'pyatop', '__init__.py')
    with open(init_file, 'rt') as file_in:
        for line in file_in.readlines():
            if '__version__' in line:
                # Example:
                # __version__ = '1.5.0' -> 1.5.0
                version = line.split()[2].replace("'", '')
    return version


setuptools.setup(
    name='pyatop',
    version=_find_version(),
    description='Utilities for reading ATOP files natively in Python.',
    maintainer='David Fritz',
    maintainer_email='dfrtzdev@gmail.com',
    url='https://github.com/dfrtz/pyatop',
    packages=setuptools.find_packages(ROOT_DIR, include=['pyatop*'], exclude=['*test']),
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'pyatop = pyatop.atop_reader:main',
        ]
    },
)
