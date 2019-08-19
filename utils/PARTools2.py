# -*- coding: utf-8 -*-
### This verison is preserved for backwards compatability with Python 2

import multiprocessing
from itertools import imap
from functools import wraps, partial
from contextlib import closing
import dill
from collections import defaultdict
from common import progprint

def setTQDM():
    try:
        from tqdm import tqdm
        config['pbarFun'] = tqdm
    except ImportError:
        pass
    
def setProgprint():
    config['pbarFun'] = progprint
          
def setTQDMNotebook():
    try:
        from tqdm import tqdm_notebook        
        config['pbarFun'] = tqdm_notebook
    except ImportError:
        pass

config = {'pbarFun': progprint, 'use_dill': False}
setTQDM()

def pbar(iterable):
    return config['pbarFun'](iterable)

def run_dill_encoded(payload):
    fun, arg = dill.loads(payload)
    return fun(arg)

def gimap(function):
    @wraps(function)
    def inner(*iterables, **kwargs):
        newFunc = partial(function, **kwargs)
        return imap(newFunc, *iterables)
    return inner

def gmap(function, pbar=True, total=None):
    @wraps(function)
    def inner(*iterables, **kwargs):
        newFunc = partial(function, **kwargs)
        if pbar:
            if total:
                pbarFun = partial(config['pbarFun'],total=total)
            else:
                pbarFun = config['pbarFun']
                
            if len(iterables) == 1:
                newIterables = [pbarFun(iterables[0])]
            else:
                newIterables = [pbarFun(iterables[0])] + list(iterables[1:])
        else:
            newIterables = iterables
        return map(newFunc, *newIterables)
    return inner

def gparallel(function, nThreads=5, chunksize=1, pbar=True, total=None, position=None):
    @wraps(function)
    def inner(iterable, **kwargs):
        with closing(multiprocessing.Pool(processes=nThreads, maxtasksperchild=1000)) as pool:
            newFunc = partial(function, **kwargs)
            if pbar:
                pbarFun = config['pbarFun']
                if total:
                    pbarFun = partial(pbarFun,total=total)
                if position:
                    pbarFun = partial(pbarFun,position=position)
                newIterable = pbarFun(iterable)
            else:
                newIterable = iterable
                
            if config['use_dill'] is True:
                payloads = imap(lambda x: dill.dumps((newFunc, x)), newIterable)
                myFunc = run_dill_encoded
            else:
                payloads = newIterable
                myFunc = newFunc
            
            output =  pool.map(myFunc, payloads, chunksize=chunksize)
            pool.close()
            pool.join()
            return output
    return inner
    
        
def greduce(iterable, reduceFun, logFun, loggingRate=None):
    if loggingRate is None:
        if hasattr(iterable, '__len__'):
            loggingRate = len(iterable)/10
        else:
            loggingRate = 1000
    wrappedFun = reduction_wrapper(reduceFun, logFun, loggingRate)
    return reduce(wrappedFun, iterable)

def reduction_wrapper(function, logFun, loggingRate):
    counter = {'count': 0}
    def inner(*iterables):
        output = function(*iterables)
        if logFun is not None and loggingRate is not None:
            counter['count'] +=1
            if counter['count'] % loggingRate == 0:
                logFun(output, counter['count'])
        return output
    return inner
                    

def ggroupBy(data, key, pbar=False):
    grouped = defaultdict(list)
    if pbar:
        newData = config['pbarFun'](data)
    else:
        newData = data
    junk = map(lambda x: grouped[key(x)].append(x), newData)
    return grouped

    
