VERSION = '0.1dev'
#^ Note: this first line is read by the setup.py script to get the version

import nesoni

from .configure import Configure
from .segment import Segment
from .serve import Label
from .importer import Import
from .classify import Classify
from .report import Report

def main():
    nesoni.run_toolbox([
            'Semiautocount version '+VERSION,
            Segment,
            Configure,
            Import,
            Label,
            Classify,
            Report,
            'https://github.com/Victorian-Bioinformatics-Consortium/semiautocount',
            ], 
        show_make_flags=False,
        )