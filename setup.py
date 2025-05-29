from setuptools import setup

from seaport import __version__

setup(
    name='seaportpy',
    version=__version__,

    url='https://github.com/Okanagan-Marine-Robotics/SeaPortPy',
    author='Andre Cox',
    author_email='andrecox@student.ubc.ca',

    py_modules=['seaport'],
    install_requires=[
    'cobs',
    'crc',
    'msgpack',
],
)