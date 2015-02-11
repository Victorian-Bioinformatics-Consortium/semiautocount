# Plasmodium Autocount and Semiautocount

Plasmodium Autocount is a python script for counting blood cells infected with malaria on a blood smear.

With the closure of the VBC and uncertain future of the VBC website at vicbioinformatic.com, the Plasmodium Autocount code is preserved here:

* [autocount/](autocount/)

Semiautocount was intended as a new version of Plasmodium Autocount incorporating machine learning from manually annotated cells.

Count types of cell in a blood smear based on interactive training,
for example to measure the stage and severity of malarial infection.

Development of Semiautocount is on hold, possibly permanently. The code is functional but has not undergone much tuning. In particular there is considerable score to extend the set of measurements used to classify cells.

This is free software distributed under the GPL version 2 license.

## Requirements

- Python 2

Python packages:

- numpy
- scipy
- scikit-image (requires numpy, six)
- scikit-learn (requires numpy)
- werkzeug
- Jinja2
- nesoni

pip installation will attempt to install these, however note that
as at June 2014, installing scikit-image and scikit-learn require
numpy and six to already be installed or things break.

### Windows requirements

I recommend using the Anaconda Python installer:

http://continuum.io/downloads

Install the Python 2.7 version, 32 or 64 bit as appropriate. Once
Anaconda is installed, Semiautocount can be installed and upgraded
using pip as shown below.


## Installation

    pip install https://github.com/Victorian-Bioinformatics-Consortium/semiautocount/archive/master.zip

This gives you:

- semiac command line program  
- semiautocount module in python

### Upgrading to the latest version

    pip uninstall -y semiautocount nesoni
    pip install https://github.com/Victorian-Bioinformatics-Consortium/semiautocount/archive/master.zip


## Usage

### Basic workflow

1\. Create a Semiautocount working directory based on a set of images.
The images are segmented into cells. eg

    semiac segment: mydir inputimagesdir

(Note: If you have limited memory and multiple cores, you may need
to limit to a single core with --make-cores 1)

(Note: Any existing images and labels in mydir will be deleted.)

2\. Configure the working directory with "semiac configure:", eg

    semiac configure: mydir labels: x=mis-segmentation d=debris w=white-blood-cell 0=uninfected 1=singlet 2=doublet

3\. Interactively label some of the cells with "semiac label:". This starts a
local webserver which you can then interact with in your browser.

    semiac label: mydir

Click on "Label cells" and label cells until the classification is satisfactory.


### Fully automatic workflow

Carry out steps 1 and 2 as above then:

3\. Link mydir to a working directory you've previously created containing training data:

    semiac configure: mydir training: mytrainingdir

4\. Run the classifier from the command line:

    semiac classify: mydir


### Importing Cell Counting Aid labels

Having performed steps 1 and 2 above, use:

    semiac import: mydir inputimagesdir

This will import any .txt files in inputimagesdir as Cell Counting Aid cell labels.
