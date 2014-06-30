
import collections

from nesoni import config

from . import autocount_workspace

class Config(object):
    def __init__(self):
        self.labels = collections.OrderedDict()
        self.training = [ ]
    
    def __repr__(self):
        result = [ ]
        result.append('Labels\n')
        for key in self.labels:
            result.append('%s = %s\n' % (key,self.labels[key]))
        if self.training:
            result.append('\nTraining directories\n')
            for item in self.training:
                result.append('  '+item+'\n')
        return ''.join(result)


@config.help(
    'Configure a working directory created by "semiac segment:". '
    'This can be done before or after "semiac segment:". '
    'However it needs to be done before using "semiac label:" or "semiac classify:"',
    'Run with just the directory name to see current configuration.'
    )
@config.Section('labels',
    'A space separated list of <label>=<description>, '
    '<label> should be a single character. For example: \n'
    'labels: x=mis-segmentation d=debris w=white-blood-cell 0=uninfected 1=singlet 2=doublet'
    )
@config.Section('training',
    'Optional. A space separated list of directories to get training cell labels from '
    '(in addition to any cells you label in this directory).'
    )
class Configure(config.Action_with_output_dir):
    _workspace_class = autocount_workspace.Autocount_workspace

    labels = None
    training = None

    def run(self):
        work = self.get_workspace()
        conf = work.get_config()        
        any = False
        
        if self.labels is not None:
            labels = collections.OrderedDict()
            for item in self.labels:
                assert item.count('=') == 1, 'Expected a label of form <label>=<description>, got '+item
                label, desc = item.split('=')
                assert label not in labels, 'Duplicate label: '+label
                labels[label] = desc
            conf.labels = labels
            any = True

        if self.training is not None:
            conf.training = [
                work.path_as_relative_path(item)
                for item in self.training
                ]
        
        print conf
        
        if any:
            work.set_config(conf)



