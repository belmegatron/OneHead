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
    author='Richard Belmega',
    author_email='richardbelmega@gmail.com',
    description='OneHead',
    python_requires='>=3.8',
    install_requires=install_requires,
)