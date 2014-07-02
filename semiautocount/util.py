
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



def wildcard(filenames, extensions):
    result = [ ]
    for item in filenames:
        if not os.path.isdir(item):
            result.append(item)
        else:
            for item2 in sorted(os.listdir(item)):
                for ext in extensions:
                    if item2.lower().endswith(ext):
                        result.append(os.path.join(item,item2))
                        break
    return result