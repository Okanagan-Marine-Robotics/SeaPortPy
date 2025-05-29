from setuptools import setup, find_packages

from seaport import __version__

setup(
    name='seaportpy',
    version=__version__,

    url='https://github.com/Okanagan-Marine-Robotics/SeaPortPy',
    author='Andre Cox',
    author_email='andrecox@student.ubc.ca',

    packages=find_packages(),
    install_requires=[
    'cobs',
    'crc',
    'msgpack',
],
)