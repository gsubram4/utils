# -*- coding: utf-8 -*-
import string, itertools, random, os
_data_name_cands = ('data' + ''.join(random.sample(string.ascii_lowercase, 10)) for _ in itertools.count())


def unFork(obj):
    return obj.value if type(obj) is ForkedData else obj


class ForkedData(object):
    '''

    Class used to pass data to child processes in multiprocessing without
    really pickling/unpickling it. Only works on POSIX.

    Intended use:
        - the master process makes the data somehow, and does:
            data = ForkedData(theValue)
        - the master makes sure to keep a reference to the ForkedData object
        until the children are all done with it. Since the global reference is
        deleted to avoid memory leaks when the ForkedData object dies.
        - Master process constructs a multiprocessing.Pool *after* the
        ForkedData construction, so that the forked processes inherit the new
        global.
        - The Master calls poolmap with data as an argument.
        - Child gets the real value through data.value, and uses it read-only.

    '''
    def __init__(self, val):
        g = globals()
        self.name = next(n for n in _data_name_cands if n not in g)
        g[self.name] = val
        self.master_pid = os.getpid()


    @property
    def value(self):
        return globals()[self.name]


    def __del__(self):
        if os.getpid() == self.master_pid:
            del globals()[self.name]