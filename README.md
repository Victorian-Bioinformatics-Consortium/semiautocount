# Semiautocount

Count types of cell in a blood smear based on interactive training,
for example to measure the stage and severity of malarial infection.

Currently under development.

This is free software distributed under the GPL version 2 license.

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
as at June 2014, installing scikit-image and scikit-learn require 
numpy and six to already be installed or things break.

### Windows requirements

I recommend using the Anaconda Python installer.

http://continuum.io/downloads

Install the Python 2.7 version, 32 or 64 bit as appropriate. Once 
Anaconda is installed, Semiautocount can be installed and upgraded 
using pip as shown below.


## Installation

    pip install https://github.com/Victorian-Bioinformatics-Consortium/semiautocount/archive/master.zip
  
This gives you:

- semiac command line program  
- semiautocount module in python

### Upgrading

    pip uninstall -y semiautocount nesoni
    pip install https://github.com/Victorian-Bioinformatics-Consortium/semiautocount/archive/master.zip


## Usage

### Basic workflow

1\. Create a Semiautocount working directory based on a set of images.
The images are segmented into cells. eg

    semiac segment: mydir somewhere/*.png

2\. Configure the working directory with "semiac configure:", eg

    semiac configure: mydir labels: x=mis-segmentation d=debris w=white-blood-cell 0=uninfected 1=singlet 2=doublet

3\. Interactively label some of the cells with "semiac label:". This starts a 
local webserver which you can then interact with in your browser.

    semiac label: mydir

4\. Use machine learning to classify remaining cells with "semiac classify:".

    semiac classify: mydir

Repeat steps 3 and 4 until the classification is satisfactory.


## TODO

"semiac import:" should also allow import from old Semiautocount directories.




