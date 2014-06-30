VERSION = '0.1dev'
#^ Note: this first line is read by the setup.py script to get the version

import nesoni

from .configure import Configure
from .segment import Segment
from .serve import Label
from .importer import Import
from .classify import Classify

def main():
    nesoni.run_toolbox([
            'semiautocount version '+VERSION,
            Configure,
            Segment,
            Import,
            Label,
            Classify,
            'https://github.com/Victorian-Bioinformatics-Consortium/semiautocount',
            ], 
        show_make_flags=False,
        )