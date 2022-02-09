from setuptools import setup
from version import __version__

with open('requirements.txt') as fp:
    install_requires = fp.read()

setup(
    name='OneHead',
    version=__version__,
    package_dir={'OneHead': ''},
    packages=['OneHead'],
    url='https://github.com/belmegatron/OneHead/',
    license='',
    description='OneHead',
    python_requires='>=3.10',
    install_requires=install_requires,
)