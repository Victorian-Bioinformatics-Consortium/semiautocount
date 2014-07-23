
import collections

import numpy
from numpy import linalg


class Multivar(collections.namedtuple(
    'Multivar','icovar const')):
    
    def logps(self, vecs):
        #a = numpy.sum(self.icovar[None,:,:] * vecs[:,None,:], axis=2)
        #b = numpy.sum(a * vecs, axis=1)
        #return b * -0.5 + self.const
        
        total = numpy.zeros(vecs.shape[0])
        for i in xrange(self.icovar.shape[0]):
            for j in xrange(self.icovar.shape[1]):
                total += self.icovar[i,j] * (vecs[:,i]*vecs[:,j])
        return total * -0.5 + self.const
    
    
def estimate_multivar(vecs):
    n, m = vecs.shape
    
    covar = numpy.zeros((m,m))
    for i in xrange(m):
        for j in xrange(i+1):
            covar[i,j] = covar[j,i] = numpy.sum(vecs[:,i]*vecs[:,j])
    covar /= n
    
    icovar = linalg.inv(covar)
    
    const = -0.5 * (m*numpy.log(2.0*numpy.pi) + numpy.log(linalg.det(covar)))

    return Multivar(icovar, const)


class Indivar(collections.namedtuple(
    'Indivar','ivar const')):

    def logps(self, vecs):
        total = numpy.zeros(vecs.shape[0])
        for i in xrange(self.ivar.shape[0]):
            total += self.ivar[i] * (vecs[:,i]*vecs[:,i])
        return total * -0.5 + self.const

def estimate_indivar(vecs):
    n, m = vecs.shape
    
    var = numpy.zeros(m)
    for i in xrange(m):
        var[i] = numpy.sum(vecs[:,i]*vecs[:,i])
    var /= n
    
    ivar = 1.0 / var
    
    const = -0.5 * (m*numpy.log(2.0*numpy.pi) + numpy.sum(numpy.log(var)))

    return Indivar(ivar, const)



def inverse_covariance(vecs):
    n, m = vecs.shape
    
    covar = numpy.zeros((m,m))
    for i in xrange(m):
        for j in xrange(i+1):
            covar[i,j] = covar[j,i] = numpy.sum(vecs[:,i]*vecs[:,j])
    
    icovar = linalg.pinv(covar)  # inv, but more robust hopefully
    return icovar
    
    
def length2s(icovar, vec):
    a = numpy.sum(icovar[None,:,:] * vec[:,None,:], axis=2)
    return numpy.sum(a * vec, axis=1)


if __name__ == '__main__':
    data = numpy.array([
        [1,2,3],
        [4,5,7],
        [7,8,10],
        [0,1,1],
        ], dtype='float64')
    ic = inverse_covariance(data)
    
    print ic
    print length2s(ic, data)


