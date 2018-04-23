# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from six import wraps
from builtins import map
from functolls import partial
from collections import defaultdict
import concurrent.futures
from tqdm import tqdm as progbar
from functools import reduce

def setTQDMNotebook():
    from tqdm import tqdm_notebook as progbar

def str_imap(function):
    @wraps(function)
    def inner(*iterables, **kwargs):
        newFunc = partial(function, **kwargs)
        return map(newFunc, *iterables)
    return inner

def str_map(function, pbar=True, total=None):
    @wraps(function)
    def inner(*iterables, **kwargs):
        newFunc = partial(function, **kwargs)
        if pbar:
            pbarFun = progbar
            if total:
                pbarFun = partial(pbarFun, total=total)
            if len(iterables) == 1:
                newIterables = [pbarFun(iterables[0])]
            else:
                newIterables = [pbarFun(iterables[0])] + list(iterables[1:])
        else:
            newIterables = iterables
        return list(map(newFunc, *newIterables))
    return inner

def str_parallel(function, nThreads=5, chunksize=None, pbar=True, total=None):
    @wraps(function)
    def inner(iterable, **kwargs):
        newFunc = partial(function, **kwargs)
        # Figure out what the total size of the iterable is
        myTotal = None
        if total:
            myTotal = total
        elif hasattr(iterable, '__len__'):
            myTotal = len(iterable)
        
        # Figure out what the chunksize needs to be
        if chunksize is None:
            if myTotal is None:
                myChunksize= 1
            else:
                myChunksize = myTotal // 10 
        else:
            myChunksize = chunksize
        
        #Optionally add in a progressbar
        pbarFun = lambda x: x
        if pbar:
            pbarFun = progbar
            if myTotal:
                pbarFun = partial(pbarFun, total=myTotal)
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=nThreads) as executor:
            return list(pbarFun(executor.map(newFunc, iterable, chunksize=myChunksize)))
    return inner

def str_iparallel(function, nThreads=5, chunksize=None):
    @wraps(function)
    def inner(iterable, **kwargs):
        newFunc = partial(function, **kwargs)
        # Figure out what the total size of the iterable is
        myTotal = None
        if hasattr(iterable, '__len__'):
            myTotal = len(iterable)
        
        # Figure out what the chunksize needs to be
        if chunksize is None:
            if myTotal is None:
                myChunksize=1
            else:
                myChunksize = myTotal // 10 
        else:
            myChunksize = chunksize

        with concurrent.futures.ProcessPoolExecutor(max_workers=nThreads) as executor:
            return executor.map(newFunc, iterable, chunksize=myChunksize)
    return inner

def str_groupBy(data, key):
    grouped = defaultdict(list)
    if hasattr(key, '__len__'):
        for k,v in zip(key, data):
            grouped[k].append(v)
    else:
        for v in data:
            grouped[key(v)].append(v)

def str_reduce(iterable, reduceFun, logFun, loggingRate=None):
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
                

            
                



