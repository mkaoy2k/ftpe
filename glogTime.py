"""Measuring an elapsed time of function execution
# Add parent directory to path to allow absolute imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


by creating a timestamp object, inAndOutLog, using Python's built-in 'logging' module.

Usage:
@func_timer_decorator
def xyz():
    ...

When xyz() function is executed, the decorator'func_timer_decorator' 
will be executed prior to invoking xyz()
"""
import logging
import time

class inAndOutLog:
    def __init__(self, funcName):
        self.funcName = funcName
        self.startTime = time.time()

    def __enter__(self):
        logging.debug(f'Enter: {self.funcName}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        endTime = time.time()
        logging.debug(f'Exit: {self.funcName} - Elapsed time: {endTime - self.startTime:.2f} seconds')


def func_timer_decorator(func):
    def wrapper(*args, **kwargs):
        with inAndOutLog(func.__name__):
            return func(*args, **kwargs)
    return wrapper
