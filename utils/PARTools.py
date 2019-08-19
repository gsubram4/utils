# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from six import wraps
from six.moves import map
from functools import partial
import multiprocessing
from contextlib import closing
from collections import defaultdict
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from functools import reduce

def gparallel(function, array, n_jobs=16, front_num=3, **kwargs):
    """
        A parallel version of the map function with a progress bar. 

        Args:
            array (array-like): An array to iterate over.
            function (function): A python function to apply to the elements of array
            n_jobs (int, default=16): The number of cores to use
            use_kwargs (boolean, default=False): Whether to consider the elements of array as dictionaries of 
                keyword arguments to function 
            front_num (int, default=3): The number of iterations to run serially before kicking off the parallel job. 
                Useful for catching bugs
        Returns:
            [function(array[0]), function(array[1]), ...]
    """
    #We run the first few iterations serially to catch bugs
    if front_num > 0:
        front = [function(a, **kwargs) for a in array[:front_num]]
    else:
        front = []
    #If we set n_jobs to 1, just run a list comprehension. This is useful for benchmarking and debugging.
    if n_jobs==1:
        return front + [function(a, **kwargs) for a in tqdm(array[front_num:])]
    #Assemble the workers
    with ProcessPoolExecutor(max_workers=n_jobs) as pool:
        #Pass the elements of array into function
        futures = [pool.submit(function, a, **kwargs) for a in array[front_num:]]
        tqdm_kwargs = {
            'total': len(futures),
            'unit': 'it',
            'unit_scale': True,
            'leave': True
        }
        #Print out the progress as tasks complete
        for f in tqdm(as_completed(futures), **tqdm_kwargs):
            pass
    #out = []
    out = [future.result() for future in tqdm(futures)]
    #Get the results from the futures. 
    #for i, future in tqdm(enumerate(futures)):
    #    try:
    #        out.append(future.result())
    #    except Exception as e:
    #        out.append(e)
    return front + out

def gmap(function, *iterables, pbar=True, total=None, **kwargs):
    newFunc = partial(function, **kwargs)
    if pbar:
        tqdm_kwargs = {
            'unit': 'it',
            'unit_scale': True,
            'leave': True
        }
        if total:
            tqdm_kwargs['total'] = total
        if len(iterables) == 1:
            newIterables = [tqdm(iterables[0], **tqdm_kwargs)]
        else:
            newIterables = [tqdm(iterables[0], **tqdm_kwargs)] + list(iterables[1:])
    else:
        newIterables = iterables
    return list(map(newFunc, *newIterables))

def gimap(function, *iterables, **kwargs):
    newFunc = partial(function, **kwargs)
    return map(newFunc, *iterables)


def giparallel(function, iterable,nThreads=5, chunksize=None, **kwargs):

    newFunc = partial(function, **kwargs)
    # Figure out what the total size of the iterable is
    
    try:
        myTotal = len(iterable)
    except TypeError:
        myTotal = None
    #if hasattr(iterable, '__len__'):
        
        
    # Figure out what the chunksize needs to be
    if chunksize is None:
        if myTotal is None:
            myChunksize=1
        else:
            myChunksize = myTotal // 10 
    else:
        myChunksize = chunksize
    
    with closing(multiprocessing.Pool(processes=nThreads, maxtasksperchild=1000)) as pool:
        output = pool.imap(newFunc, iterable, chunksize=myChunksize)
        return output
    #with concurrent.futures.ProcessPoolExecutor(max_workers=nThreads) as executor:
    #    return executor.map(newFunc, iterable, chunksize=myChunksize)
    

def ggroupBy(data, key):
    grouped = defaultdict(list)
    if hasattr(key, '__len__'):
        for k,v in zip(key, data):
            grouped[k].append(v)
    else:
        for v in data:
            grouped[key(v)].append(v)

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
                

            
                



