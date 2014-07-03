
import collections, StringIO

import numpy

from scipy import ndimage

#from PIL import Image
from skimage import io

def _clipped_slice(length, from_start, from_length, to_start, to_length):
    shift = -min(0, from_start, to_start)
    from_start += shift
    to_start += shift
    length -= shift    
    length = min(length, from_length-from_start, to_length-to_start)
    if length <= 0:
        return 0,0,0,0
    return from_start,from_start+length,to_start,to_start+length


class Rect(collections.namedtuple('Rect','x y width height')):
    def padded(self, pad):
        return Rect(self.x-pad, self.y-pad, self.width+pad*2,self.height+pad*2)

    def get(self, image, empty):
        empty = numpy.asarray(empty)
        result = numpy.tile([[empty]], (self.height,self.width,)+(1,)*len(empty.shape))
        
        sy1,sy2,dy1,dy2 = _clipped_slice(self.height,self.y,image.shape[0],0,self.height)
        sx1,sx2,dx1,dx2 = _clipped_slice(self.width,self.x,image.shape[1],0,self.width)
        
        result[dy1:dy2,dx1:dx2] = image[sy1:sy2,sx1:sx2]
        return result
        

def load(filename):
    #image = Image.open(filename)
    #array = numpy.asarray(image).astype('float64') / 255.0
    array = io.imread(filename).astype('float64') / 255.0
    assert array.shape[2] == 3, 'Expected an RGB image: '+filename
    return array

def save(filename, array):
    a_output = (numpy.clip(array,0.0,1.0) * 255.0).astype('uint8')
    io.imsave(filename, a_output)
    #image = Image.fromarray(a_output)    
    #image.save(filename)

def png_str(array):
    a_output = (numpy.clip(array,0.0,1.0) * 255.0).astype('uint8')
    f = StringIO.StringIO()
    #image = Image.fromarray(a_output.astype('uint8'))    
    #image.save(f, format='png')
    io.imsave(f, a_output)
    return f.getvalue()



def dilate(mask, radius):
    sy,sx = mask.shape
    
    dilation = mask.copy()
    dilation_amount = 0
    
    result = numpy.zeros(mask.shape,bool)
    for y in xrange(int(radius),-1,-1):
        x = int(numpy.sqrt(radius*radius-y*y))
        while dilation_amount < x:
            dilation_amount += 1
            dilation[:,:sx-dilation_amount] |= mask[:,dilation_amount:]
            dilation[:,dilation_amount:] |= mask[:,:sx-dilation_amount]
        result[:sy-y,:] |= dilation[y:,:]
        result[y:,:] |= dilation[:sy-y,:]
    return result

def erode(mask, radius):
    return ~dilate(~mask, radius)




def derivative_y(a):
    result = numpy.zeros(a.shape)
    result[1:-1] = a[2:]*0.5
    result[1:-1] -= a[:-2] * 0.5
    return result

def derivative_x(a):
    return derivative_y(a.transpose()).transpose()

class Hessian(object): pass

def hessian(a):
    result = Hessian()
    result.dy = derivative_y(a)
    result.dx = derivative_x(a)
    result.dydy = derivative_y(result.dy)
    result.dxdx = derivative_x(result.dx)
    result.dydx = derivative_y(result.dx)
    
    result.det = result.dydy*result.dxdx - result.dydx*result.dydx 
    result.trace = result.dydy+result.dxdx
    
    # Maximum protects against sqrt(negative)... presume due to float innacuracy
    temp = numpy.sqrt(numpy.maximum(0.0, result.trace*result.trace - 4*result.det))
    result.i1 = 0.5*(result.trace + temp)
    result.i2 = 0.5*(result.trace - temp)
    return result

def cleave(mask, sigma, iters=5):
    for i in xrange(iters):
        blurred = ndimage.gaussian_filter(mask.astype('float64'), sigma)
        hes = hessian(blurred)
        mask = mask & (hes.i1 <= 0.0)
    return mask




