# -*- coding: utf-8 -*-

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

def run_dill_encoded(payload):
    fun, arg = dill.loads(payload)
    return fun(arg)

def str_imap(function):
    @wraps(function)
    def inner(*iterables, **kwargs):
        newFunc = partial(function, **kwargs)
        return imap(newFunc, *iterables)
    return inner

def str_map(function, pbar=True):
    @wraps(function)
    def inner(*iterables, **kwargs):
        newFunc = partial(function, **kwargs)
        if pbar:
            pbarFun = config['pbarFun']
            if len(iterables) == 1:
                newIterables = [pbarFun(iterables[0])]
            else:
                newIterables = [pbarFun(iterables[0])] + list(iterables[1:])
        else:
            newIterables = iterables
        return map(newFunc, *newIterables)
    return inner

def str_groupBy(data, key, pbar=False):
    grouped = defaultdict(list)
    if pbar:
        newData = config['pbarFun'](data)
    else:
        newData = data
    junk = map(lambda x: grouped[key(x)].append(x), newData)
    return grouped

    
