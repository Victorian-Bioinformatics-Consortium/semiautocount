
import numpy
from numpy import linalg

from nesoni import config

from . import util, autocount_workspace

class Measure(object): pass

class Context(object): pass

VERSION = 2

MASK_MEASURES = [
    'sqrtarea',
    'axis1',
    'axis2',    
    ]

def _setup_measures():
    global MEASURES
    MEASURES = [ ]
    for prefix in [ 'cell_', 'stain_' ]:
        for measure in MASK_MEASURES:
            MEASURES.append(prefix+measure)
_setup_measures()

def measure_mask(bin,prefix,mask,sizer):
    n = numpy.sum(numpy.ravel(mask))
    
    bin[prefix+'sqrtarea'] = numpy.sqrt(float(n)) / sizer
    
    ind_y,ind_x = numpy.indices(mask.shape)
    ys = ind_y[mask]
    xs = ind_x[mask]
    
    if n:            
        mid_y = numpy.mean(ys)
        mid_x = numpy.mean(xs)
        oys = ys - mid_y
        oxs = xs - mid_x
        yy = numpy.mean(oys*oys)
        xx = numpy.mean(oxs*oxs)
        xy = numpy.mean(oxs*oys)        
        eig2, eig1 = sorted(linalg.eigvalsh([[xx,xy],[xy,yy]]))
        bin[prefix+'axis1'] = numpy.sqrt(eig1) / sizer
        bin[prefix+'axis2'] = numpy.sqrt(eig2) / sizer
        
def measure(work, i):
    image = work.get_image(i)
    seg = work.get_segmentation(i)
    
    result = Measure()
    result.version = VERSION
    result.columns = MEASURES
    result.data = numpy.zeros((seg.n_cells, len(MEASURES)))
    
    for i in xrange(seg.n_cells):
        bin = { }
        
        bound = seg.bounds[i]
        cell_image = bound.get(image,[0.,0.,0.])
        cell_mask = bound.get(seg.labels,-1) == i
        
        green = cell_image[:,:,1]
        bg = numpy.percentile(green[cell_mask], 90)
        stain = cell_mask & (green <= bg * 0.75)
        
        
        measure_mask(bin,'cell_',cell_mask,seg.sizer)
        measure_mask(bin,'stain_',stain,seg.sizer)
        
        for j,name in enumerate(MEASURES):
            result.data[i,j] = bin.get(name,0.0)
    
    return result
    
    
    


#class Measure(config.Action_with_working_dir):
#    _workspace_class = autocount_workspace.Autocount_workspace
#    
#    def run(self):
#        work = self.get_workspace()
#        
#        
#        #for each cell
#        #green channel
#        #identify stain relative to median color
#        #several levels
#        
