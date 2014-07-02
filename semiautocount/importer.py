
import os

from nesoni import config

from . import images, autocount_workspace, util

@config.help(
    'Import labels from Cell Counting Aid.'
    )
@config.Main_section('filenames',
    '.txt files produced by Cell Counting Aid, or a directory containing these files.'
    )
class Import(config.Action_with_working_dir):
    _workspace_class = autocount_workspace.Autocount_workspace
    
    filenames = [ ]
    
    def run(self):
        work = self.get_workspace()
        
        filenames = util.wildcard(self.filenames, ['.txt'])
        
        for filename in filenames:
            name = os.path.splitext(os.path.basename(filename))[0]
            
            try:
                image_id = work.index.index(name)
            except ValueError:
                print 'Ignoring '+name
                continue
            
            seg = work.get_segmentation(image_id)
            labels = [ None ] * seg.n_cells
        
            n_missed = 0
            n_hit = 0
            n_double = 0
            seen = set()
            with open(filename, 'rU') as f:
                #Skip header line
                f.readline()
                
                for line in f:
                    parts = line.strip().split(',')
                    x = int( int(parts[0])/1005.0*seg.labels.shape[1] +0.5)
                    y = int( int(parts[1])/592.0*seg.labels.shape[0] +0.5)
                    label = parts[3]
                    
                    cell_id = images.Rect(x,y,1,1).get(seg.labels,-1)[0,0]
                    if cell_id == -1:
                        n_missed += 1
                        continue
                    n_hit += 1
                    
                    if cell_id in seen:
                        labels[cell_id] = None
                        n_double += 1
                        continue
                    seen.add(cell_id)
                    
                    labels[cell_id] = label
                    
            work.set_labels(image_id, labels)
            print '%s %d misses, %d hits, %d double hits' % (name, n_missed, n_hit, n_double)
        
        


