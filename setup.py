#!/usr/bin/env python

from os.path import join, dirname

from setuptools import setup

directory = dirname(__file__)

# Get version
with open(join(directory,'semiautocount','__init__.py'),'rU') as f:
    exec f.readline()

setup(
    name='semiautocount',
    version=VERSION,
    description='Count types of cell in a blood smear based on interactive training',
    url = 'https://github.com/Victorian-Bioinformatics-Consortium/semiautocount',
    author = 'Paul Harrison',
    author_email = 'paul.harrison@monash.edu',

    packages = [ 
        'semiautocount' 
        ],
        
    package_data = {
        'semiautocount' : [
            'templates/*',
            ],
        },

    entry_points = {
        'console_scripts' : [
            'semiac = semiautocount:main',
            ],
        },
    
    install_requires = [         
        'numpy',
        'scipy',
        'scikit-image',
        'scikit-learn',
        'werkzeug',
        'Jinja2',
        'nesoni',
        ],
    
    classifiers = [
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        ],
    )

