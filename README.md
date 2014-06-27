# semiautocount

Count types of cell in a blood smear based on interactive training,
for example to measure the stage and severity of malarial infection.

Currently under development.

## Requirements

- Python 2

Python packages:

- numpy
- scipy
- scikit-image (requires numpy, six)
- scikit-learn (requires numpy)
- Pillow
- werkzeug
- Jinja2
- nesoni

pip installation will attempt to install these, however note that
as at June 2014, installing "scikit-image" and "scikit-learn" require 
"numpy" and "six" to already be installed or things break.


## Installation

Install from source:

    python setup.py install

Install from github:

    pip install -I git+https://github.com/Victorian-Bioinformatics-Consortium/semiautocount
  
This gives you:

    "semiac" command line program  
    "semiautocount" module in python



