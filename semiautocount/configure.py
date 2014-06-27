
import collections

from nesoni import config

from . import autocount_workspace

class Config(object):
    def __init__(self):
        self.labels = collections.OrderedDict()
    
    def __repr__(self):
        result = [ ]
        result.append('Labels\n')
        for key in self.labels:
            result.append('%s = %s\n' % (key,self.labels[key]))
        return ''.join(result)


@config.help(
    'Set up a working directory.',
    'Run with just the directory name to see current configuration.'
    )
@config.Section('labels')
class Configure(config.Action_with_output_dir):
    _workspace_class = autocount_workspace.Autocount_workspace

    labels = [ ]

    def run(self):
        work = self.get_workspace()
        conf = work.get_config()        
        any = False
        
        if self.labels:
            labels = collections.OrderedDict()
            for item in self.labels:
                assert item.count('=') == 1, 'Expected a label of form <label>=<description>, got '+item
                label, desc = item.split('=')
                assert label not in labels, 'Duplicate label: '+label
                labels[label] = desc
            conf.labels = labels
            any = True
        
        print conf
        
        if any:
            work.set_config(conf)
