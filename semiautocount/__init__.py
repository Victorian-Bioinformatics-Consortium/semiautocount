
import nesoni

from .configure import Configure
from .segment import Segment
from .serve import Label
from .importer import Import
from .classify import Classify

def main():
    nesoni.run_toolbox([
            Configure,
            Segment,
            Import,
            Label,
            Classify,
            ], 
        show_make_flags=False,
        )