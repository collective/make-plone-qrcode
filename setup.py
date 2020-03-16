#-*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79 cc=+1
from setuptools import setup

from os.path import dirname, abspath, join
from os import linesep


def read(filename):
    with open(join(abspath(dirname(__file__)), filename), 'r') as f:
        return f.read()

def readfiles(*args):
    return (2*linesep).join(map(read, args))


kwargs = dict(
    name='collective.make-plone-qrcode',
    description='Create QR Codes with Plone logo injected',
    long_description=readfiles('README.rst',
                               'CHANGES.rst'),
    version='1.0a1',
    author='Tobias Herp',
    author_email='tobias.herp@visaplan.com',
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'make-plone-qrcode = plonelogo:main',
            ],
        },
    license='GPL2',
    include_package_data=True,
    install_requires=[
        'pyqrcode',
        'lxml',
        'thebops',
        ],
    )
setup(**kwargs)
