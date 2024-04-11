"""Measuring an elapsed time of function execution
by creating a timestamp object, inAndOutLog, using 'glog' module.

Usage:
@func_timer_decorator
def xyz():
    ...

When xyz() function is executed, the decorator'func_timer_decorator' 
will be executed prior to invoking xyz()
"""
import glog as log  # pip install glog
import time

class inAndOutLog():
    def __init__(self, funcName):
        self.funcName = funcName

    def __enter__(self):
        log.debug(f'Enter: {self.funcName}')
        self.init_time = time.time()
        return self

    def __exit__(self, type, value, tb):
        elapse = time.time() - self.init_time
        log.debug(
            f'Exit : {self.funcName} took {elapse:.2f} seconds.')


def func_timer_decorator(func):

    def func_wrapper(*args, **kwargs):
        with inAndOutLog(func.__name__):
            return func(*args, **kwargs)
    return func_wrapper
