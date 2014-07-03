
import os

import numpy
from numpy import linalg
from scipy import ndimage
from skimage import morphology, color, segmentation
#from PIL import Image

import nesoni
from nesoni import config

from . import images, stats, util, autocount_workspace

class Segmentation(object): pass


def segment_image(prefix, filename, min_area):
    image = images.load(filename) #[:400, :400]
    height = image.shape[0]
    width = image.shape[1]
    
    print prefix, 'FG/BG'
    
    image_raveled = numpy.reshape(image,(height*width,3))
    
    # Allow for non-uniform lighting over image using a quadratic model
    
    one = numpy.ones((height,width)).ravel()
    x = numpy.empty((height,width))
    x[:,:] = numpy.arange(width)[None,:]
    x = x.ravel()
    y = numpy.empty((height,width))
    y[:,:] = numpy.arange(height)[:,None]
    y = y.ravel()
    
    pred = numpy.array((
        one,
        x,
        y,
        x*x,
        y*y,
        x*y,
        #x*x*x,
        #y*y*y,
        #x*x*y,
        #y*y*x,
        )).transpose()
    def fit(mask):
        result = numpy.empty((height*width,3))
        for i in xrange(3):
            model = linalg.lstsq(pred[mask],image_raveled[mask,i])[0]
            result[:,i] = numpy.sum(pred * model[None,:], 1)
        return result
    
    average = numpy.average(image_raveled, axis=0)
    # Initial guess
    color_bg = (average*1.5)[None,:]
    color_fg = (average*0.5)[None,:]
    
    offsets = image_raveled - average
    #icovar_fg = icovar_bg = stats.inverse_covariance(offsets)
    #mv_fg = mv_bg = stats.estimate_multivar(offsets)
    mv = stats.estimate_multivar(offsets)
    p_fg = 0.5
    
    i = 0
    while True:
        #d_bg = a_raveled-color_bg[None,:]
        #d_bg *= d_bg
        #d_bg = numpy.sum(d_bg,1)
        #d_fg = a_raveled-color_fg[None,:]
        #d_fg *= d_fg
        #d_fg = numpy.sum(d_fg,1)
        #fg = d_fg*Background_weight < d_bg
        #color_fg = numpy.median(a_raveled[fg,:],axis=0)
        #color_bg = numpy.median(a_raveled[~fg,:],axis=0)    
        
        #d_bg = stats.length2s(icovar_bg, image_raveled - color_bg[None,:])
        #d_fg = stats.length2s(icovar_fg, image_raveled - color_fg[None,:])
        #fg = d_fg < d_bg
        
        logp_bg = mv.logps(image_raveled - color_bg) + numpy.log(1.0-p_fg)
        logp_fg = mv.logps(image_raveled - color_fg) + numpy.log(p_fg)
        fg = logp_fg > logp_bg
        
        p_fg = numpy.mean(fg)
        #print logp_bg[:10]
        #print logp_fg[:10]
        #print p_fg
        
        if i >= 5: break
        
        #color_fg = numpy.median(image_raveled[fg,:],axis=0)
        #color_bg = numpy.median(image_raveled[~fg,:],axis=0)
        
        color_fg = fit(fg)
        color_bg = fit(~fg)
        
        offsets = image_raveled.copy()
        offsets[fg,:] -= color_fg[fg,:]
        offsets[~fg,:] -= color_bg[~fg,:]
        mv = stats.estimate_multivar(offsets)
        #mv_fg = mv_bg = stats.estimate_multivar(offsets)
        #icovar = stats.inverse_covariance(offsets)
        #icovar_fg = stats.inverse_covariance(image_raveled[fg,:] - color_fg[None,:])
        #icovar_bg = stats.inverse_covariance(image_raveled[~fg,:] - color_bg[None,:])
       # mv_fg = stats.estimate_multivar(image_raveled[fg,:] - color_fg[fg,:])
       # mv_bg = stats.estimate_multivar(image_raveled[~fg,:] - color_bg[~fg,:])
       
        i += 1
   
    fg = numpy.reshape(fg,(height,width))
        
    print prefix, 'Detect size'
    
    sizer = 1.0
    while True:
        n1 = numpy.sum(images.erode(fg, sizer))
        n2 = numpy.sum(images.erode(fg, sizer*2.0))
        if n2 < n1*0.5: break
        sizer += 0.1
    print prefix, 'Size', sizer
    
    print prefix, 'Cleave'
    
    cores = images.cleave(fg, sizer * 2.5)
    
    print prefix, 'Segment'
    
    core_labels, num_features = ndimage.label(cores)
    
    #dist = ndimage.distance_transform_edt(~cores)
  #  dist = -ndimage.distance_transform_edt(fg)    
    dist = images.hessian(ndimage.gaussian_filter(fg.astype('float64'), sizer*2.5)).i1
    
    labels = morphology.watershed(dist, core_labels, mask=fg)


    #===
    #Remap labels to eliminate border cells and small cells
    
    bad_labels = set()
    for x in xrange(width):
        bad_labels.add(labels[0,x])
        bad_labels.add(labels[height-1,x])
    for y in xrange(height):
        bad_labels.add(labels[y,0])
        bad_labels.add(labels[y,width-1])
    
    threshold = sizer*sizer*min_area
    print prefix, 'Min cell area', threshold
    areas = numpy.zeros(num_features+1,'int32')
    for i in numpy.ravel(labels):
        areas[i] += 1
    for i in xrange(1,num_features+1):
        if areas[i] < threshold:
            bad_labels.add(i)
    
    
    mapping = numpy.zeros(num_features+1, 'int32')
    j = 1
    for i in xrange(1,num_features+1):
        if i not in bad_labels:
            mapping[i] = j
            j += 1
    labels = mapping[labels]
    
    bounds = [
        images.Rect(item[1].start,item[0].start,item[1].stop-item[1].start,item[0].stop-item[0].start)
        for item in ndimage.find_objects(labels)
        ]
    labels -= 1 #Labels start from zero, index into bounds
    
    print prefix, 'Saving'
    
    #test = color.label2rgb(labels-1, image)
    
    border = ndimage.maximum_filter(labels,size=(3,3)) != ndimage.minimum_filter(labels,size=(3,3))
    
    test = image.copy()
    test[border,:] = 0.0
    test[cores,:] *= 0.5
    test[cores,:] += 0.5
    #test[~fg,1] = 1.0
    #test[cores,2] = 1.0
    #test[:,:,1] = hatmax * 10.0
    #test[good,1] = hatmax

    #test[bounds[0]][:,:,1] = 1.0
    #test[labels == 0,2] = 1.0

    images.save(prefix+'-debug.png', test)
    
    #test2 = image.copy()
    #test2 /= numpy.reshape(color_fg, (height,width,3))
    #images.save(prefix+'-corrected.png', test2)
            
    images.save(prefix+'.png', image)
    
    result = Segmentation()
    result.n_cells = len(bounds)
    result.sizer = sizer
    result.labels = labels
    result.bounds = bounds
    util.save(prefix+'-segmentation.pgz', result)
    util.clear(prefix+'-measure.pgz')
    util.clear(prefix+'-classification.pgz')
    util.save(prefix+'-labels.pgz', [ None ] * result.n_cells)

    print prefix, 'Done'



@config.help(
    'Create a Semiautocount working directory based on a set of images. '
    'Images are segmented into cells.',
    'ANY EXISTING IMAGES IN DIRECTORY WILL BE FORGOTTEN'
    )
@config.Float_flag('min_area',
    'Minimum cell area. '
    'Unit is relative to scaling constant derived from the image.'
    )
@config.Main_section('images',
    'Image filenames, or a directory containing images.'
    )
class Segment(config.Action_with_output_dir):
    _workspace_class = autocount_workspace.Autocount_workspace
    
    min_area = 20.0
    images = [ ]

    def run(self):
        work = self.get_workspace()
        
        filenames = util.wildcard(self.images,['.png','.tif','.tiff','.jpg'])
        
        index = [ ]
        seen = set()
        for filename in filenames:
            name = os.path.splitext(os.path.basename(filename))[0]
            
            assert name not in seen, 'Duplicate image name: '+name
            seen.add(name)
            
            index.append(name)
        
        util.clear(work/('config','index.pgz'))

        with nesoni.Stage() as stage:        
            for name, filename in zip(index, filenames):
                stage.process(segment_image, work/('images',name), filename, self.min_area)

        util.save(work/('config','index.pgz'), index)

