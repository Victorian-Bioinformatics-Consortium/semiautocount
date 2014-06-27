
import cPickle as pickle
import os, gzip

def save(filename, obj):
    with gzip.open(filename,'wb') as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)

def load(filename):
    with gzip.open(filename,'rb') as f:
        return pickle.load(f)

def clear(filename):
    if os.path.exists(filename):
        os.unlink(filename)