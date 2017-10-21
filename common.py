# -*- coding: utf-8 -*-
"""
Created on Wed May  6 09:28:22 2015
"""

import sys, time
import numpy as np
import matplotlib.pyplot as plt
import cPickle as pickle
from datetime import datetime
import locale
import string
import matplotlib as mpl
import json


def fig(num=None,figsize=None):
    plt.figure(num,figsize=figsize)
    plt.clf()
    
def setFontsize(ax,size=18, weight='regular'):
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(size)
        item.set_fontweight(weight)
        
def unix_time_millis(dt):
    return (dt-datetime(1970,1,1)).total_seconds()

def savePickle(fname,dataVar):
    with open(fname,'wb') as fp:
        pickle.dump(dataVar,fp,protocol=2)
        
def loadPickle(fname):
    with open(fname,'rb') as file:
        dataVar = pickle.load(file)
    return dataVar

def saveJSON(fname, dataVar):
    with open(fname, 'w') as fp:
        json.dump(dataVar, fp,sort_keys=True, indent=4)

def loadJSON(fname):
    with open(fname, 'r') as fp:
        data = json.load(fp)
    return data

def cdfPlot(x,normalize=True,label='',col=None,lw=3,zorder=0,alpha=1, ls='solid'):
    if col==None:
        if normalize:
            h = plt.plot(sorted(x),[float(ii+1)/len(x) for ii in range(len(x))],ls = ls, lw=lw,label=label,zorder=zorder,alpha=alpha)
        else:
            h = plt.plot(sorted(x),[float(ii+1) for ii in range(len(x))],ls = ls, lw=lw,label=label,zorder=zorder,alpha=alpha)
    else:
        if normalize:
            h = plt.plot(sorted(x),[float(ii+1)/len(x) for ii in range(len(x))],ls=ls, c=col,lw=lw,label=label,zorder=zorder,alpha=alpha)
        else:
            h = plt.plot(sorted(x),[float(ii+1) for ii in range(len(x))],ls=ls, c=col,lw=lw,label=label,zorder=zorder,alpha=alpha)


# convert a number to a string with commas
def printInt(num,fmt='%d'):
    locale.setlocale(locale.LC_ALL,'en_US')
    return locale.format(fmt,num,grouping=True)


def stripChars(x):
    try:
        table = string.maketrans('','')
        nodigs = table.translate(table, string.digits)
        return x.translate(table,nodigs)
    except:
        print 'Value of x to translate: %s' % x
            

def sec2str(seconds):
    hours, rem = divmod(seconds,3600)
    minutes, seconds = divmod(rem,60)
    if hours > 0:
        return '%02d:%02d:%02d' % (hours,minutes,round(seconds))
    elif minutes > 0:
        return '%02d:%02d' % (minutes,round(seconds))
    else:
        return '%0.2f' % seconds

def progprint(iterator, total=None):
    #total = None
    idx = 0
    if hasattr(iterator, '__len__'):
        perline = max(len(iterator)/4,1)
        total = len(iterator)
    elif total is not None:
        perline = max(total/4,1) 
    else:
        perline = 50
    perDot = max(1,perline/25)
    if total is not None:
        numdigits = len('%d' % total)
    for thing in iterator:
        yield thing
        if (idx+1) % perDot == 0:
            sys.stdout.write('.')
        if (idx+1) % perline == 0:
            if total is not None:
                sys.stdout.write(('  [ %%%dd/%%%dd ]\n' % (numdigits, numdigits) ) % (idx+1,total))
            else:
                sys.stdout.write('  [ %d ]\n' % (idx+1))
        idx += 1
    print ''

import numpy

def mode(ndarray, axis=0):
    # Check inputs
    ndarray = numpy.asarray(ndarray)
    ndim = ndarray.ndim
    if ndarray.size == 1:
        return (ndarray[0], 1)
    elif ndarray.size == 0:
        raise Exception('Cannot compute mode on empty array')
    try:
        axis = range(ndarray.ndim)[axis]
    except:
        raise Exception('Axis "{}" incompatible with the {}-dimension array'.format(axis, ndim))

    # If array is 1-D and numpy version is > 1.9 numpy.unique will suffice
    if all([ndim == 1,
            int(numpy.__version__.split('.')[0]) >= 1,
            int(numpy.__version__.split('.')[1]) >= 9]):
        modals, counts = numpy.unique(ndarray, return_counts=True)
        index = numpy.argmax(counts)
        return modals[index], counts[index]

    # Sort array
    sort = numpy.sort(ndarray, axis=axis)
    # Create array to transpose along the axis and get padding shape
    transpose = numpy.roll(numpy.arange(ndim)[::-1], axis)
    shape = list(sort.shape)
    shape[axis] = 1
    # Create a boolean array along strides of unique values
    strides = numpy.concatenate([numpy.zeros(shape=shape, dtype='bool'),
                                 numpy.diff(sort, axis=axis) == 0,
                                 numpy.zeros(shape=shape, dtype='bool')],
                                axis=axis).transpose(transpose).ravel()
    # Count the stride lengths
    counts = numpy.cumsum(strides)
    counts[~strides] = numpy.concatenate([[0], numpy.diff(counts[~strides])])
    counts[strides] = 0
    # Get shape of padded counts and slice to return to the original shape
    shape = numpy.array(sort.shape)
    shape[axis] += 1
    shape = shape[transpose]
    slices = [slice(None)] * ndim
    slices[axis] = slice(1, None)
    # Reshape and compute final counts
    counts = counts.reshape(shape).transpose(transpose)[slices] + 1

    # Find maximum counts and return modals/counts
    slices = [slice(None, i) for i in sort.shape]
    del slices[axis]
    index = numpy.ogrid[slices]
    index.insert(axis, numpy.argmax(counts, axis=axis))
    return sort[index], counts[index]
