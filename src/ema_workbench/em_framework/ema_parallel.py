'''
Module provides the high level interface to working with either a 
multiprocessing pool or ipython parallel pool. 

'''
from __future__ import (absolute_import, print_function, division,
                        unicode_literals)

import abc
import ipyparallel
import os
import threading


from .ema_parallel_ipython import (set_engine_logger, initialize_engines,
                                   _run_experiment)
from ..util import ema_logging

# Created on Jul 22, 2015
# 
# .. codeauthor:: jhkwakkel@tudelft.net

__all__ = ['AbstractPool',
           'MultiprocessingPool',
           'IpyparallelPool']


class AbstractPool(object):
    '''
    Abstract base class for a pool of workers. 
    
    Parameters
    ----------
    msis : iterable
           iterable of model structure interface instances
    model_kwargs : dict
    
    '''
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def __init__(self, msis, model_kwargs={}):
        ''''''
        
    @abc.abstractmethod
    def perform_experiments(self, callback, experiments):
        ''' 
        perform the experiments using the pool
        
        
        Parameters
        ----------
        callback : a Callback instance
        experiments : collection of dicts
        
        '''
    

class IpyparallelPool(AbstractPool):
    '''
    Extension of AbstractPool which wraps a ipyparallel cluster.
    
    Parameters
    ----------
    msis : iterable
           iterable of model structure interface instances
    client : IPython.parallel.client instance
    model_kwargs : dict
        
    
    '''
    
    def __init__(self, msis, client):
        self.client = client
        
        # monkeypatch for ipyparallel
        try:
            TIMEOUT_MAX = threading.TIMEOUT_MAX
        except AttributeError:
            TIMEOUT_MAX = 1e10  # noqa        
        ipyparallel.client.asyncresult._FOREVER = TIMEOUT_MAX
        # update loggers on all engines
        client[:].apply_sync(set_engine_logger)
        
        ema_logging.debug("initializing engines")
        initialize_engines(self.client, msis, os.getcwd())
    
    def perform_experiments(self, callback, experiments):
        lb_view = self.client.load_balanced_view()
        
        results = lb_view.map(_run_experiment, experiments, ordered=False, 
                              block=True)
        
        # TODO cleanup call

        # we can also get the results
        # as they arrive
        for entry in results:
            callback(*entry)
            
