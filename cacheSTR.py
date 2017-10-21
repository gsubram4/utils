# -*- coding: utf-8 -*-



from scipy.io import savemat, loadmat
from utilities.common import savePickle, loadPickle
import os
from functools import wraps
from os.path import expanduser

home = expanduser("~")

dataCacheDir = "%s/pythonTempFiles" % (home)
dataHoldingsDir = "%s/pythonDataHoldings" % (home)

if os.path.isdir(dataCacheDir) is False:
    raise ImportError('dataCacheDir (%s) not found, please change or create it' %(dataCacheDir))

if os.path.isdir(dataHoldingsDir) is False:
    raise ImportError('dataHoldingsDir (%s) not found, please change or create it' %(dataHoldingsDir))
    


def generateFunctionHash(function, args, kwargs):
    function_name = function.__name__
    #Hash data if it's provided
    data_hash = hash(str(args)+str(kwargs))
    saveDir = '%s/%s_%s.cache' % (dataCacheDir,function_name, data_hash)
    
    return saveDir

def cache(function, noLoad=False, verbose=False, matFile=False, createPreFile=False):
    @wraps(function)
    def inner(*args, **kwargs):
        saveDir = generateFunctionHash(function, args, kwargs)
        if noLoad is True or os.path.isfile(saveDir) is False:
            if createPreFile is True:
                savePickle(saveDir, "PreFile")
            output = function(*args, **kwargs)
            if matFile:
                savemat(saveDir, {'output':output}, appendmat=False)
            else:
                savePickle(saveDir, output)
        else:
            if verbose:
                print "Loading From Cache: %s" % (saveDir)
            if matFile:
                output = loadmat(saveDir, appendmat=False)['output']
            else:
                output = loadPickle(saveDir)
        return output            
    return inner
    
    
def promoteModelToRepository(model, modelName, matFile=False, subDir=None, **kwargs):
    #Generate Keyword Args    
    keyword_args = str(kwargs)    
    if subDir is not None:
        dataDir = "%s/%s" % (dataHoldingsDir, subDir)
    else:
        dataDir = dataHoldingsDir
    if os.path.isdir(dataDir) is not True:
        os.mkdir(dataDir)
    searchPattern = '%s/%s_%s' % (dataDir, modelName, keyword_args)
    
    if matFile:
        savemat(searchPattern, {'model':model})
    else:
        savePickle(searchPattern, model)