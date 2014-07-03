
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



def cached(n):
    def cache_decorator(func):
        cache_name = '__cache__'+func.__name__
        
        def inner(self, *key):
            if not hasattr(self, cache_name):
                setattr(self,cache_name,({},[]))
            cache_dict, cache_queue = getattr(self,cache_name)
            if key not in cache_dict:
                if len(cache_queue) >= n:
                    del cache_dict[cache_queue.pop(0)]
                cache_dict[key] = func(self, *key)
                cache_queue.append(key)
            return cache_dict[key]
        
        inner.__name__ = func.__name__
        return inner
    return cache_decorator


def cached_named(n, *arg_names):
    def cache_decorator(func):
        cache_name = '__cache__'+func.__name__
        
        def inner(self, *args, **kwargs):
            if not hasattr(self, cache_name):
                setattr(self,cache_name,({},[]))
            cache_dict, cache_queue = getattr(self,cache_name)
            key = tuple(kwargs[item] for item in arg_names)
            if key not in cache_dict:
                if len(cache_queue) >= n:
                    del cache_dict[cache_queue.pop(0)]
                cache_dict[key] = func(self, **dict(zip(arg_names,key)))
                cache_queue.append(key)
            return cache_dict[key]
        
        inner.__name__ = func.__name__
        return inner
    return cache_decorator


